#!/bin/bash

# NoPhish Simple Deployment Script
# Deploys NoPhish with HTTP access initially

set -e

echo "🚀 Deploying NoPhish Professional..."

# Create necessary directories
mkdir -p ssl certbot-www logs

# Check if SSL certificates exist
if [ -f "ssl/live/account-login.help/fullchain.pem" ] && [ -f "ssl/live/account-login.help/privkey.pem" ]; then
    echo "🔒 SSL certificates found, using HTTPS configuration"
    cp nginx-ssl.conf frontend/nginx-ssl.conf
    SSL_PORTS="- 443:443"
    echo "📍 Site will be available at: https://account-login.help"
else
    echo "🌐 No SSL certificates found, using HTTP configuration"
    cp nginx-http.conf frontend/nginx-simple.conf
    SSL_PORTS=""
    echo "📍 Site will be available at: http://localhost:8080"
    echo "💡 Run ./setup-ssl.sh later to obtain SSL certificates"
fi

# Update docker-compose with SSL configuration
echo "📝 Updating Docker Compose configuration..."
sed -i "s|./nginx-ssl.conf:/etc/nginx/nginx.conf|./frontend/nginx-simple.conf:/etc/nginx/nginx.conf|" docker-compose.yml
sed -i "s|- \"8080:80\"|$SSL_PORTS|" docker-compose.yml

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose down
docker-compose up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

# Test connectivity
echo "🧪 Testing connectivity..."
if curl -f http://localhost:8080/ > /dev/null 2>&1; then
    echo "✅ Frontend is accessible at: http://localhost:8080"
else
    echo "❌ Frontend is not accessible"
fi

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is accessible at: http://localhost:8000"
else
    echo "❌ Backend API is not accessible"
fi

# Test API through frontend
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✅ API proxy is working correctly"
else
    echo "❌ API proxy is not working"
fi

echo ""
echo "🎉 NoPhish deployment completed!"
echo ""
echo "📋 Service Information:"
echo "   Frontend: http://localhost:8080"
echo "   Backend API: http://localhost:8000"
echo "   API through frontend: http://localhost:8080/api/"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Update services: docker-compose up --build -d"
echo ""
echo "📁 Important Directories:"
echo "   SSL certificates: ./ssl/live/account-login.help/"
echo "   Application logs: ./logs/"
echo "   Certbot webroot: ./certbot-www/"
echo ""
echo "🔒 SSL Setup:"
echo "   If you have SSL certificates, run: ./setup-ssl.sh"
echo "   Otherwise, the system will work with HTTP"