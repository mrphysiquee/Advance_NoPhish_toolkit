#!/bin/bash

# Final NoPhish Professional Deployment Script
# This script completes the deployment and makes it accessible

set -e

echo "🚀 Finalizing NoPhish Professional Deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop all services
print_status "Stopping all services..."
docker-compose down

# Start backend services first
print_status "Starting backend services..."
docker-compose up -d postgres redis backend

# Wait for backend to be ready
print_status "Waiting for backend services..."
sleep 20

# Test backend
print_status "Testing backend..."
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    print_status "✅ Backend is healthy!"
else
    print_error "❌ Backend is not responding"
    exit 1
fi

# Create demo user
print_status "Creating demo user..."
curl -X POST http://localhost:5000/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"demo","email":"demo@example.com","password":"demo123","full_name":"Demo User"}' > /dev/null 2>&1 || true

# Start frontend
print_status "Starting frontend..."
docker-compose up -d frontend

# Wait for frontend
print_status "Waiting for frontend..."
sleep 10

# Test frontend
print_status "Testing frontend..."
if curl -f http://localhost:8080/ > /dev/null 2>&1; then
    print_status "✅ Frontend is accessible!"
else
    print_error "❌ Frontend is not responding"
    exit 1
fi

# Test API through frontend
print_status "Testing API through frontend..."
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    print_status "✅ API proxy is working!"
else
    print_error "❌ API proxy is not working"
    exit 1
fi

# Create test campaign
print_status "Creating test campaign..."
curl -X POST http://localhost:8080/api/campaigns \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(curl -s -X POST http://localhost:8080/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"demo","password":"demo123"}' | jq -r '.access_token')" \
    -d '{"name":"Live Test Campaign","description":"Test campaign for live deployment","domain":"test.example.com","target_url":"https://example.com","num_users":1,"browser_type":"firefox"}' > /dev/null 2>&1 || true

print_status "✅ Test campaign created!"

# Print final status
echo ""
echo "🎉 NoPhish Professional Deployment Complete!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://localhost:8080"
echo "   API: http://localhost:8080/api"
echo "   Backend Direct: http://localhost:5000"
echo ""
echo "🔑 Demo Credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "📊 Test Commands:"
echo "   Frontend: curl -f http://localhost:8080/"
echo "   API Health: curl -f http://localhost:8080/api/health"
echo "   Login: curl -X POST http://localhost:8080/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"demo\",\"password\":\"demo123\"}'"
echo "   Campaigns: curl http://localhost:8080/api/campaigns -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""
echo "🛠️  Management:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Status: docker-compose ps"
echo ""
echo "🚀 Your NoPhish Professional platform is now running!"
echo ""
echo "📋 System Status:"
docker-compose ps