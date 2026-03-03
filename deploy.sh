#!/bin/bash

# NoPhish Professional Deployment Script
# This script sets up and deploys the NoPhish Professional platform

set -e

echo "🚀 Starting NoPhish Professional Deployment..."

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ssl
mkdir -p logs
mkdir -p certbot-www
mkdir -p database

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating environment file..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration before starting the services"
    print_warning "Required configurations:"
    print_warning "  - POSTGRES_PASSWORD: Secure password for PostgreSQL"
    print_warning "  - SECRET_KEY: JWT secret key (change in production)"
    print_warning "  - TELEGRAM_BOT_TOKEN: Your Telegram bot token"
    read -p "Press Enter after configuring .env file..."
fi

# Stop any existing containers
print_status "Stopping existing containers..."
docker-compose down

# Build and start services
print_status "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if services are running
print_status "Checking service status..."
docker-compose ps

# Check database health
print_status "Checking database health..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U nophish_user -d nophish > /dev/null 2>&1; then
        print_status "Database is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Database failed to start. Check logs with: docker-compose logs postgres"
        exit 1
    fi
    sleep 2
done

# Run database migrations if needed
print_status "Running database migrations..."
docker-compose exec backend python -c "
from sqlalchemy import create_engine, text
import os
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\''))
    tables = result.fetchall()
    if len(tables) == 0:
        print('Database is empty, running initialization...')
        with open('/app/database/init.sql', 'r') as f:
            conn.execute(text(f.read()))
        conn.commit()
    else:
        print('Database already initialized')
"

# Set up SSL certificates
print_status "Setting up SSL certificates..."
if [ ! -f "ssl/live/account-login.help/fullchain.pem" ]; then
    print_warning "SSL certificates not found. Getting Let's Encrypt certificates..."
    
    # Start nginx temporarily for certbot
    docker-compose up -d frontend
    
    # Wait for nginx to start
    sleep 10
    
    # Get SSL certificate
    docker-compose run --rm certbot certonly --webroot -w /var/www/certbot \
        --email admin@account-login.help --agree-tos --no-eff-email -d account-login.help
    
    # Restart nginx with new certificates
    docker-compose restart frontend
else
    print_status "SSL certificates already exist"
fi

# Check if backend is responding
print_status "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        print_status "Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Backend failed to start. Check logs with: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done

# Check if frontend is responding
print_status "Checking frontend health..."
for i in {1..30}; do
    if curl -f -k https://localhost:443/ > /dev/null 2>&1; then
        print_status "Frontend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Frontend failed to start. Check logs with: docker-compose logs frontend"
        exit 1
    fi
    sleep 2
done

# Print deployment summary
echo ""
echo "🎉 NoPhish Professional Deployment Complete!"
echo ""
echo "📋 Service URLs:"
echo "  - Frontend: https://account-login.help"
echo "  - API: https://account-login.help/api"
echo "  - Health Check: http://localhost:5000/health"
echo ""
echo "🔑 Default Login:"
echo "  - Username: admin"
echo "  - Password: admin (change immediately after first login)"
echo ""
echo "📊 Management Commands:"
echo "  - View logs: docker-compose logs -f [service]"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo "  - Update: docker-compose pull && docker-compose up -d"
echo ""
echo "🔧 Configuration:"
echo "  - Edit .env file to change configuration"
echo "  - SSL certificates are renewed automatically"
echo ""
echo "🚀 Your NoPhish Professional platform is now live!"