#!/bin/bash
set -e

DOMAIN="${PANEL_DOMAIN:-localhost}"

# Replace placeholder in nginx config
sed -i "s/PANEL_DOMAIN/$DOMAIN/g" /etc/nginx/nginx.conf

# Create empty dynamic config files (will be populated when campaigns launch)
mkdir -p /etc/nginx/conf.d
echo "# No active campaign - no upstream" > /etc/nginx/conf.d/upstream_revproxy.conf
echo "# No active campaign - no phishing routes" > /etc/nginx/conf.d/phishing_routes.conf

# Check if SSL cert exists for this domain
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "[!] No SSL cert found for $DOMAIN"
    echo "[*] Generating self-signed cert for initial startup..."
    mkdir -p "/etc/letsencrypt/live/$DOMAIN"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "/etc/letsencrypt/live/$DOMAIN/privkey.pem" \
        -out "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" \
        -subj "/CN=$DOMAIN" 2>/dev/null
    echo "[*] Self-signed cert created. Run certbot to get a real cert."
fi

echo "[+] Starting nginx for domain: $DOMAIN"
exec nginx -g "daemon off;"
