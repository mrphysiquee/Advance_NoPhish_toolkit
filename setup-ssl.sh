#!/bin/bash

# SSL Certificate Setup for NoPhish Professional
# This script obtains Let's Encrypt SSL certificates for the domain

set -e

echo "🔒 Setting up SSL certificates for account-login.help..."

# Check if domain is accessible
if ! curl -f http://account-login.help > /dev/null 2>&1; then
    echo "❌ Domain account-login.help is not accessible"
    echo "Please ensure the domain is properly configured and accessible"
    exit 1
fi

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Stop frontend temporarily
echo "🛑 Stopping frontend for certificate setup..."
docker-compose stop frontend

# Start nginx without SSL for challenge
echo "🚀 Starting nginx for Let's Encrypt challenge..."
docker run --rm \
  -p 80:80 \
  -v "$(pwd)/certbot-www:/var/www/certbot" \
  -v "$(pwd)/ssl:/etc/letsencrypt" \
  nginx:alpine

# Obtain SSL certificate
echo "📋 Obtaining SSL certificate..."
docker run --rm \
  -v "$(pwd)/certbot-www:/var/www/certbot" \
  -v "$(pwd)/ssl:/etc/letsencrypt" \
  certbot/certbot:latest \
  certonly --webroot -w /var/www/certbot \
  --email admin@account-login.help \
  --agree-tos --no-eff-email \
  -d account-login.help

# Check if certificate was obtained
if [ -f "ssl/live/account-login.help/fullchain.pem" ]; then
    echo "✅ SSL certificate obtained successfully!"
else
    echo "❌ Failed to obtain SSL certificate"
    exit 1
fi

# Create nginx configuration with SSL
echo "📝 Creating SSL-enabled nginx configuration..."
cat > frontend/nginx-ssl.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 50m;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=63072000" always;

    # HTTP -> HTTPS redirect
    server {
        listen 80;
        server_name account-login.help;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name account-login.help;

        ssl_certificate /etc/letsencrypt/live/account-login.help/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/account-login.help/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 1d;

        # React frontend
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API proxy to FastAPI backend
        location /api/ {
            proxy_pass http://backend:5000/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # Timeout settings
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Rebuild frontend with SSL configuration
echo "🏗️  Rebuilding frontend with SSL support..."
docker build -f frontend/Dockerfile -t nophish-frontend ./frontend

# Start frontend with SSL
echo "🚀 Starting frontend with SSL..."
docker-compose up -d frontend

# Wait for services to start
echo "⏳ Waiting for SSL services to start..."
sleep 10

# Test SSL connection
echo "🔒 Testing SSL connection..."
if curl -f -k https://localhost:8443/ > /dev/null 2>&1; then
    echo "✅ SSL is working correctly!"
else
    echo "❌ SSL configuration failed"
    exit 1
fi

# Set up certbot renewal
echo "⏰ Setting up automatic certificate renewal..."
cat > certbot-renew.sh << 'EOF'
#!/bin/bash
# Certbot renewal script

docker run --rm \
  -v "$(pwd)/certbot-www:/var/www/certbot" \
  -v "$(pwd)/ssl:/etc/letsencrypt" \
  certbot/certbot:latest \
  renew --webroot -w /var/www/certbot

docker-compose restart frontend
EOF

chmod +x certbot-renew.sh

# Add to crontab for automatic renewal
echo "0 12 * * * $(pwd)/certbot-renew.sh" | crontab -

echo "🎉 SSL setup completed successfully!"
echo ""
echo "📋 SSL Information:"
echo "   Domain: account-login.help"
echo "   Certificate: $(pwd)/ssl/live/account-login.help/fullchain.pem"
echo "   Private Key: $(pwd)/ssl/live/account-login.help/privkey.pem"
echo ""
echo "🌐 Access URLs:"
echo "   HTTPS: https://account-login.help"
echo "   HTTP: http://account-login.help (redirects to HTTPS)"
echo ""
echo "🔄 Certificate renewal:"
echo "   Manual: $(pwd)/certbot-renew.sh"
echo "   Automatic: Renewal scheduled daily at 12:00 PM"
echo ""
echo "🔧 Management:"
echo "   View certificates: ls -la ssl/live/account-login.help/"
echo "   Check expiration: openssl x509 -in ssl/live/account-login.help/fullchain.pem -text -noout | grep Not"