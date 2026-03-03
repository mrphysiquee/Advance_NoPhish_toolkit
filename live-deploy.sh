#!/bin/bash

# NoPhish Professional - Live Deployment Script
# This script deploys NoPhish Professional live on account-login.help

set -e

echo "🚀 Starting NoPhish Professional Live Deployment on account-login.help..."

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
    print_error "Please ensure the domain is properly configured and accessible"
    exit 1
fi

print_status "✅ Domain account-login.help is accessible"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p certbot-www
mkdir -p ssl
mkdir -p logs

# Stop existing services
print_status "Stopping existing services..."
docker-compose down

# Build and start services without SSL first
print_status "Building and starting services without SSL..."
docker-compose up -d postgres redis backend

# Wait for services to start
print_status "Waiting for backend services to start..."
sleep 20

# Check backend health
print_status "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        print_status "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Backend failed to start. Check logs with: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done

# Start frontend without SSL for certificate challenge
print_status "Starting frontend for certificate challenge..."
docker-compose up -d frontend

# Wait for frontend to start
print_status "Waiting for frontend to start..."
sleep 10

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

# Rebuild frontend with SSL configuration
print_status "Rebuilding frontend with SSL configuration..."
docker-compose build frontend

# Stop frontend and restart with SSL
print_status "Restarting frontend with SSL..."
docker-compose stop frontend
docker-compose up -d frontend

# Wait for SSL services to start
print_status "Waiting for SSL services to start..."
sleep 15

# Test SSL connection
print_status "Testing SSL connection..."
if curl -f -k https://localhost:443/ > /dev/null 2>&1; then
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

# Create test user
print_status "Creating demo user..."
curl -X POST http://localhost/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"demo","email":"demo@example.com","password":"demo123","full_name":"Demo User"}' > /dev/null 2>&1 || true

# Set up certbot renewal
print_status "Setting up automatic certificate renewal..."
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

# Add to crontab for automatic renewal (remove existing first)
print_status "Setting up automatic certificate renewal..."
(crontab -l 2>/dev/null | grep -v certbot-renew.sh; echo "0 12 * * * $(pwd)/certbot-renew.sh") | crontab -

# Create startup script
print_status "Creating startup script..."
cat > start.sh << 'EOF'
#!/bin/bash
# NoPhish Professional startup script

echo "🚀 Starting NoPhish Professional..."
cd "$(dirname "$0")"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Check status
echo "🔍 Checking service status..."
docker-compose ps

echo "🎉 NoPhish Professional is running!"
echo "🌐 Frontend: https://account-login.help"
echo "🔧 API: https://account-login.help/api"
EOF

chmod +x start.sh

# Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash
# NoPhish Professional stop script

echo "🛑 Stopping NoPhish Professional..."
cd "$(dirname "$0")"

docker-compose down

echo "✅ NoPhish Professional stopped."
EOF

chmod +x stop.sh

# Print deployment summary
echo ""
echo "🎉 NoPhish Professional Live Deployment Complete!"
echo ""
echo "🌐 Live Access Information:"
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
echo "   View logs: docker-compose logs -f [service]"
echo "   Restart: docker-compose restart"
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