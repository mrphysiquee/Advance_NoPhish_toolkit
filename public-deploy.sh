#!/bin/bash

# NoPhish Public Deployment Script
# Sets up NoPhish to be publicly accessible on account-login.help with SSL

set -e

echo "🚀 Deploying NoPhish Professional on account-login.help..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if domain is accessible
print_status "Checking domain accessibility..."
if ! curl -f http://account-login.help > /dev/null 2>&1; then
    print_error "Domain account-login.help is not accessible"
    print_error "Please ensure the domain is properly configured and points to this server"
    exit 1
fi

print_status "✅ Domain account-login.help is accessible"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ssl certbot-www logs

# Create nginx configuration for HTTP challenge
print_status "Creating nginx configuration for HTTP challenge..."
cat > nginx-http.conf << 'EOF'
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

    # HTTP server for Let's Encrypt challenge
    server {
        listen 80;
        server_name account-login.help;

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

        # Let's Encrypt challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
    }
}
EOF

# Start services with HTTP configuration
print_status "Starting services with HTTP configuration..."
docker-compose up -d postgres redis backend

# Wait for backend services to start
print_status "Waiting for backend services to start..."
sleep 20

# Start frontend with HTTP configuration
print_status "Starting frontend for certificate challenge..."
docker run --rm \
  -v "$(pwd)/frontend/build:/usr/share/nginx/html" \
  -v "$(pwd)/nginx-http.conf:/etc/nginx/nginx.conf" \
  -v "$(pwd)/certbot-www:/var/www/certbot" \
  --name nginx-challenge \
  -p 80:80 \
  nginx:alpine

# Obtain SSL certificate
print_status "Obtaining SSL certificate..."
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
    print_status "✅ SSL certificate obtained successfully!"
else
    print_error "❌ Failed to obtain SSL certificate"
    exit 1
fi

# Create SSL-enabled nginx configuration
print_status "Creating SSL-enabled nginx configuration..."
cp nginx-ssl.conf frontend/nginx-ssl.conf

# Update docker-compose for SSL
print_status "Updating Docker Compose for SSL..."
sed -i 's|- "8080:80"|- "80:80"\n      - "443:443"|' docker-compose.yml
sed -i 's|./frontend/nginx-simple.conf:/etc/nginx/nginx.conf|./frontend/nginx-ssl.conf:/etc/nginx/nginx.conf|' docker-compose.yml

# Rebuild and start with SSL
print_status "Rebuilding and starting services with SSL..."
docker-compose down
docker-compose up --build -d

# Wait for SSL services to start
print_status "Waiting for SSL services to start..."
sleep 15

# Test SSL connection
print_status "Testing SSL connection..."
if curl -f -k https://localhost/ > /dev/null 2>&1; then
    print_status "✅ SSL is working correctly!"
else
    print_error "❌ SSL configuration failed"
    exit 1
fi

# Test API through SSL
print_status "Testing API through SSL..."
if curl -f -k https://localhost/api/health > /dev/null 2>&1; then
    print_status "✅ API proxy is working through SSL!"
else
    print_error "❌ API proxy is not working through SSL"
    exit 1
fi

# Create startup script
print_status "Creating management scripts..."
cat > start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting NoPhish Professional..."
cd "$(dirname "$0")"
docker-compose up -d
echo "✅ NoPhish Professional is running!"
echo "🌐 Frontend: https://account-login.help"
echo "🔧 API: https://account-login.help/api"
EOF

cat > stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping NoPhish Professional..."
cd "$(dirname "$0")"
docker-compose down
echo "✅ NoPhish Professional stopped."
EOF

cat > restart.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting NoPhish Professional..."
cd "$(dirname "$0")"
docker-compose down
docker-compose up --build -d
echo "✅ NoPhish Professional restarted!"
EOF

chmod +x start.sh stop.sh restart.sh

# Create test user
print_status "Creating demo user..."
curl -X POST https://localhost/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"demo","email":"demo@example.com","password":"demo123","full_name":"Demo User"}' > /dev/null 2>&1 || true

# Print deployment summary
echo ""
echo "🎉 NoPhish Professional Public Deployment Complete!"
echo ""
echo "🌐 Public Access Information:"
echo "   Frontend: https://account-login.help"
echo "   API: https://account-login.help/api"
echo "   Health Check: https://account-login.help/health"
echo ""
echo "🔑 Demo Credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "📊 Test API Endpoints:"
echo "   Health: curl -k https://account-login.help/api/health"
echo "   Login: curl -X POST -k https://account-login.help/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"demo\",\"password\":\"demo123\"}'"
echo "   Campaigns: curl -k https://account-login.help/api/campaigns -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""
echo "🛠️  Management Commands:"
echo "   Start: ./start.sh"
echo "   Stop: ./stop.sh"
echo "   Restart: ./restart.sh"
echo "   View logs: docker-compose logs -f [service]"
echo "   Update: docker-compose pull && docker-compose up -d"
echo ""
echo "🔒 SSL Information:"
echo "   Certificate: $(pwd)/ssl/live/account-login.help/fullchain.pem"
echo "   Private Key: $(pwd)/ssl/live/account-login.help/privkey.pem"
echo "   Auto-renewal: Daily at 12:00 PM"
echo ""
echo "📋 System Status:"
docker-compose ps
echo ""
echo "🚀 Your NoPhish Professional platform is now live on https://account-login.help!"