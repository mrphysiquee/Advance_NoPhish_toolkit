from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required

from ..models import db, Link, Campaign

links_bp = Blueprint("links", __name__)


@links_bp.route("/links")
@login_required
def manage():
    campaign_id = request.args.get("campaign_id", type=int)
    if campaign_id:
        links = Link.query.filter_by(campaign_id=campaign_id).all()
        campaign = Campaign.query.get(campaign_id)
    else:
        links = Link.query.all()
        campaign = None
    return render_template("links/manage.html", links=links, campaign=campaign)


@links_bp.route("/links/<int:link_id>/track")
def track(link_id):
    """Track a link click and redirect to the actual phishing URL."""
    link = Link.query.get_or_404(link_id)
    link.click_count += 1
    db.session.commit()
    return redirect(link.url)


@links_bp.route("/links/<int:link_id>/regenerate", methods=["POST"])
@login_required
def regenerate(link_id):
    import uuid
    link = Link.query.get_or_404(link_id)
    campaign = Campaign.query.get(link.campaign_id)
    scheme = "https" if campaign.ssl else "http"
    token = str(uuid.uuid4())
    if campaign.custom_param:
        link.url = f"{scheme}://{campaign.domain}/v{link.user_num}/{campaign.custom_param}"
    else:
        link.url = f"{scheme}://{campaign.domain}/v{link.user_num}/oauth2/authorize?access-token={token}"
    link.click_count = 0
    db.session.commit()
    flash("Link regenerated.", "success")
    return redirect(url_for("links.manage", campaign_id=campaign.id))
