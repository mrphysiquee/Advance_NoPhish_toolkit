import os
import subprocess

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required

from ..models import db, Domain

domains_bp = Blueprint("domains", __name__)


@domains_bp.route("/domains")
@login_required
def list_domains():
    domains = Domain.query.order_by(Domain.created_at.desc()).all()
    return render_template("domains/list.html", domains=domains)


@domains_bp.route("/domains/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form.get("name", "").strip().lower()
        purpose = request.form.get("purpose", "campaign")
        cert_method = request.form.get("cert_method", "manual")

        if not name:
            flash("Domain name is required.", "error")
            return render_template("domains/add.html")

        if Domain.query.filter_by(name=name).first():
            flash("Domain already exists.", "error")
            return render_template("domains/add.html")

        domain = Domain(
            name=name,
            purpose=purpose,
            cert_method=cert_method,
        )

        if cert_method == "manual":
            cert_path = request.form.get("cert_path", "").strip()
            key_path = request.form.get("key_path", "").strip()
            if cert_path and key_path:
                domain.cert_path = cert_path
                domain.key_path = key_path
                domain.ssl_enabled = True
                # Verify files exist
                if os.path.exists(cert_path) and os.path.exists(key_path):
                    domain.verified = True
                else:
                    flash("Warning: Cert/key files not found at specified paths. SSL will fail until valid files are provided.", "warning")
        elif cert_method == "letsencrypt":
            # Will be issued after DNS verification
            domain.cert_path = f"/etc/letsencrypt/live/{name}/fullchain.pem"
            domain.key_path = f"/etc/letsencrypt/live/{name}/privkey.pem"

        db.session.add(domain)
        db.session.commit()

        if cert_method == "letsencrypt":
            flash(f"Domain '{name}' added. Click 'Issue SSL' to obtain a Let's Encrypt certificate (DNS must point to this server first).", "success")
        else:
            flash(f"Domain '{name}' added successfully.", "success")

        return redirect(url_for("domains.list_domains"))

    return render_template("domains/add.html")


@domains_bp.route("/domains/<int:domain_id>/issue-ssl", methods=["POST"])
@login_required
def issue_ssl(domain_id):
    domain = Domain.query.get_or_404(domain_id)

    if domain.cert_method != "letsencrypt":
        flash("This domain uses manual certificates.", "warning")
        return redirect(url_for("domains.list_domains"))

    # Run certbot to issue cert
    try:
        result = subprocess.run(
            [
                "certbot", "certonly", "--standalone",
                "--non-interactive", "--agree-tos",
                "--email", "admin@" + domain.name,
                "-d", domain.name,
                "--preferred-challenges", "http",
            ],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode == 0:
            domain.ssl_enabled = True
            domain.verified = True
            domain.cert_path = f"/etc/letsencrypt/live/{domain.name}/fullchain.pem"
            domain.key_path = f"/etc/letsencrypt/live/{domain.name}/privkey.pem"
            db.session.commit()
            flash(f"SSL certificate issued for {domain.name}!", "success")
        else:
            error_msg = result.stderr or result.stdout
            flash(f"Certbot failed: {error_msg[:300]}", "error")

    except subprocess.TimeoutExpired:
        flash("Certbot timed out. Ensure DNS points to this server and ports 80/443 are open.", "error")
    except FileNotFoundError:
        flash("Certbot not found. Install it or use the nginx container which includes certbot.", "error")

    return redirect(url_for("domains.list_domains"))


@domains_bp.route("/domains/<int:domain_id>/verify", methods=["POST"])
@login_required
def verify(domain_id):
    domain = Domain.query.get_or_404(domain_id)

    # Check DNS resolution
    try:
        result = subprocess.run(
            ["dig", "+short", domain.name, "A"],
            capture_output=True, text=True, timeout=10,
        )
        resolved_ips = result.stdout.strip().split("\n")
        server_ip = _get_server_ip()

        if server_ip in resolved_ips:
            domain.verified = True
            db.session.commit()
            flash(f"DNS verified! {domain.name} resolves to {server_ip}.", "success")
        else:
            flash(f"DNS mismatch: {domain.name} resolves to {', '.join(resolved_ips)} but server IP is {server_ip}. Update your DNS.", "warning")
    except FileNotFoundError:
        # dig not available, try basic check
        import socket
        try:
            resolved = socket.gethostbyname(domain.name)
            server_ip = _get_server_ip()
            if resolved == server_ip:
                domain.verified = True
                db.session.commit()
                flash(f"DNS verified! {domain.name} resolves to {server_ip}.", "success")
            else:
                flash(f"DNS mismatch: {domain.name} resolves to {resolved} but server IP is {server_ip}.", "warning")
        except socket.gaierror:
            flash(f"Could not resolve {domain.name}. Check your DNS settings.", "error")
    except Exception as e:
        flash(f"Verification failed: {str(e)}", "error")

    return redirect(url_for("domains.list_domains"))


@domains_bp.route("/domains/<int:domain_id>/delete", methods=["POST"])
@login_required
def delete(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    db.session.delete(domain)
    db.session.commit()
    flash(f"Domain '{domain.name}' deleted.", "info")
    return redirect(url_for("domains.list_domains"))


@domains_bp.route("/domains/<int:domain_id>/set-panel", methods=["POST"])
@login_required
def set_as_panel(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    # Unset any existing panel domain
    Domain.query.filter_by(purpose="panel").update({"purpose": "campaign"})
    domain.purpose = "panel"
    db.session.commit()
    flash(f"'{domain.name}' set as panel domain. Restart the nginx container with PANEL_DOMAIN={domain.name} for it to take effect.", "success")
    return redirect(url_for("domains.list_domains"))


def _get_server_ip():
    """Get external IP of this server."""
    try:
        result = subprocess.run(
            ["curl", "-s", "ifconfig.me"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"
