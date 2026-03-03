from flask import Flask, request
from flask_cors import CORS
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

from .config import Config
from .models import db, AdminUser


login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(AdminUser, int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # Add session configuration
    # SESSION_COOKIE_SECURE=False so login works over HTTP (NGINX handles HTTPS)
    app.config.update(
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=1800,  # 30 minutes
    )
    
    # Security headers (skip for API routes to not break CORS preflight)
    @app.after_request
    def add_security_headers(response):
        if not request.path.startswith('/api/'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    CORS(app, resources={r"/api/*": {
        "origins": "*",
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": False,
    }})
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        import os as _os
        db.create_all()
        # Read credentials from env at runtime (not from Config class attrs which
        # are evaluated at import time and may differ from runtime env)
        admin_user = _os.environ.get("ADMIN_USERNAME", "angler")
        admin_pass = _os.environ.get("ADMIN_PASSWORD", "angler")
        try:
            existing = AdminUser.query.filter_by(username=admin_user).first()
            if existing:
                existing.password_hash = generate_password_hash(admin_pass)
                db.session.commit()
                print(f"[+] Admin password updated for: {admin_user}")
            else:
                admin = AdminUser(
                    username=admin_user,
                    password_hash=generate_password_hash(admin_pass),
                )
                db.session.add(admin)
                db.session.commit()
                print(f"[+] Default admin created: {admin_user} / {admin_pass}")
        except Exception:
            db.session.rollback()

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.campaigns import campaigns_bp
    from .routes.links import links_bp
    from .routes.monitoring import monitoring_bp
    from .routes.api import api_bp
    from .routes.domains import domains_bp
    from .routes.rest_api import rest_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(domains_bp)
    app.register_blueprint(rest_bp)

    # Setup logging
    from .logging_config import setup_logging
    loggers = setup_logging(app)
    app.loggers = loggers
    
    # Start background collector
    from .collector import start_collector
    start_collector(app)

    return app
