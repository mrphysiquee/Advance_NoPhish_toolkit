# NoPhish Installation Guide

Complete installation and deployment guide for NoPhish phishing simulation platform.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Server Setup](#server-setup)
4. [Docker Installation](#docker-installation)
5. [NoPhish Deployment](#nophish-deployment)
6. [SSL Certificate Setup](#ssl-certificate-setup)
7. [Initial Configuration](#initial-configuration)
8. [Verification](#verification)
9. [Post-Installation](#post-installation)

---

## System Requirements

### Hardware Requirements

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| CPU | 2 cores | 4+ cores | Additional cores for VNC containers |
| RAM | 4 GB | 8+ GB | Each VNC container512MB |
| needs ~ Storage | 20 GB | 50+ GB SSD | Logs, containers, databases |
| Bandwidth | 100 Mbps | 1 Gbps | For smooth VNC sessions |

### Software Requirements

| Component | Version | Required |
|-----------|---------|----------|
| OS | Ubuntu 20.04+ | Yes |
| Docker | 24.0+ | Yes |
| Docker Compose | v2.0+ | Yes |
| Nginx | 1.18+ | Yes |
| Python | 3.8+ | Yes |
| Git | 2.0+ | Yes |

### Network Requirements

```
Required Ports:
├── 22    → SSH (Server Management)
├── 80    → HTTP (Let's Encrypt)
└── 443   → HTTPS (Main Access)

DNS Requirements:
└── A Record → yourdomain.com → Server IP
```

---

## Prerequisites Installation

### Step 1: Update System

```bash
# Update package list
sudo apt update

# Upgrade system
sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git nginx certbot \
    software-properties-common apt-transport-https \
    ca-certificates gnupg lsb-release
```

### Step 2: Install Python 3

```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Verify installation
python3 --version
# Output: Python 3.x.x
```

### Step 3: Install Git

```bash
# Install Git
sudo apt install -y git

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify
git --version
# Output: git version 2.x.x
```

---

## Docker Installation

### Option A: Install Docker (Recommended)

```bash
# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Verify Docker installation
docker --version
# Output: Docker version 24.x.x

docker compose version
# Output: Docker Compose version v2.x.x
```

### Option B: Install Docker via Script

```bash
# Download Docker install script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run install script
sudo sh get-docker.sh

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Cleanup
rm get-docker.sh
```

### Verify Docker Installation

```bash
# Run test container
docker run --rm hello-world

# Should output: "Hello from Docker!"
```

---

## Server Setup

### Step 1: Configure Firewall (Optional but Recommended)

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 2: Create Project Directory

```bash
# Create project directory
sudo mkdir -p /opt/nophish
cd /opt/nophish

# Set ownership (replace 'user' with your username)
sudo chown -R user:user /opt/nophish
```

### Step 3: Clone Repository

```bash
# Clone NoPhish repository
git clone https://github.com/your-repo/NoPhish.git .

# Verify files
ls -la
```

---

## SSL Certificate Setup

### Option A: Let's Encrypt (Free) - Recommended

```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificate will be saved to:
# /etc/letsencrypt/live/yourdomain.com/

# Copy certificates to project
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/

# Set proper permissions
sudo chmod 644 ssl/*.pem

# Start nginx
sudo systemctl start nginx
```

### Option B: Purchased SSL Certificate

```bash
# Create ssl directory
mkdir -p ssl

# Upload your certificate files:
#   fullchain.pem  (certificate + intermediate chain)
#   privkey.pem    (private key)

# Set permissions
chmod 600 ssl/privkey.pem
chmod 644 ssl/fullchain.pem
```

### Auto-Renewal Setup

```bash
# Test auto-renewal (dry run)
sudo certbot renew --dry-run

# Add cron job for auto-renewal
sudo crontab -e

# Add this line:
# 0 0,12 * * * certbot renew --pre-hook "systemctl stop nginx" --post-hook "systemctl start nginx"
```

---

## NoPhish Deployment

### Step 1: Environment Configuration

```bash
# Copy environment example
cp .env.example .env

# Edit environment file
nano .env
```

Update these values:

```env
# Database
POSTGRES_PASSWORD=your_secure_password_here

# Security
SECRET_KEY=your_secret_key_minimum_32_characters

# Domain
PANEL_DOMAIN=yourdomain.com

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
```

### Step 2: Generate Secret Key

```bash
# Generate secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copy output to SECRET_KEY in .env
```

### Step 3: Build Docker Images

```bash
# Build all images
docker compose build

# This may take 10-15 minutes on first run
```

### Step 4: Start Services

```bash
# Start all containers in detached mode
docker compose up -d

# Check status
docker compose ps

# Expected output:
# NAME                IMAGE               STATUS
# nophish-nginx       nophish-nginx      Up
# nophish-panel       nophish-panel      Up
# nophish-postgres    postgres:15        Up
# nophish-redis      redis:7-alpine     Up
```

### Step 5: View Logs

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f panel
docker compose logs -f nginx

# View last 100 lines
docker compose logs --tail=100
```

---

## Initial Configuration

### Access Admin Panel

```
URL: https://yourdomain.com
Username: admin
Password: changeme123
```

**⚠️ IMPORTANT: Change password immediately after first login!**

### Create First Campaign

1. Login to admin panel
2. Navigate to "Campaigns"
3. Click "New Campaign"
4. Fill in details:
   - **Name**: Test Campaign
   - **Target URL**: https://accounts.google.com
   - **Browser**: Chrome
   - **Device**: Desktop
   - **Redirect URL**: https://www.google.com
5. Click "Create"
6. Note the generated phishing URL

### Test VNC Connection

```bash
# Access desktop VNC
https://yourdomain.com/vnc/demo/conn.html

# Access mobile VNC
https://yourdomain.com/vnc/demo/mconn.html
```

---

## Verification

### Check All Services

```bash
# 1. Check container status
docker compose ps

# 2. Check nginx is running
docker exec nophish-nginx nginx -t

# 3. Check database connection
docker exec nophish-panel python3 -c "from app import db; print('DB OK')"

# 4. Check API health
curl -f https://yourdomain.com/api/health

# 5. Check SSL certificate
curl -fvI https://yourdomain.com 2>&1 | grep "SSL certificate verify"
```

### Test Endpoints

```bash
# Test main page
curl -I https://yourdomain.com

# Test API
curl -I https://yourdomain.com/api/campaigns

# Test VNC path
curl -I https://yourdomain.com/vnc/demo/conn.html
```

### Check Logs for Errors

```bash
# Panel errors
docker compose logs panel | grep -i error

# Nginx errors
docker compose logs nginx | grep -i error

# Database errors
docker compose logs postgres | grep -i error
```

---

## Post-Installation

### Update Admin Password

1. Login to admin panel
2. Go to Profile/Settings
3. Change password

### Configure Telegram Notifications (Optional)

```bash
# Edit .env file
nano .env

# Add Telegram bot token
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id

# Restart services
docker compose restart panel
```

### Set Up Backups

```bash
# Create backup script
nano backup.sh

# Add:
#!/bin/bash
DATE=$(date +%Y%m%d)
docker exec nophish-postgres pg_dump -U nophish_user nophish > backup_$DATE.sql
tar -czf backup_$DATE.tar.gz backup_$DATE.sql ssl/

# Make executable
chmod +x backup.sh

# Add to cron (weekly)
crontab -e
# 0 2 * * 0 /opt/nophish/backup.sh
```

### Monitoring Setup

```bash
# Install ctop (container monitoring)
sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.7/ctop-0.7.7-linux-amd64 -O /usr/local/bin/ctop
sudo chmod +x /usr/local/bin/ctop

# Run ctop
ctop
```

---

## Troubleshooting

### Common Issues

#### Issue: "Port 80 already in use"

```bash
# Find what's using port 80
sudo lsof -i :80

# Stop the service
sudo systemctl stop nginx
# OR
sudo systemctl stop apache2
```

#### Issue: "Database connection refused"

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Wait for database to be ready
# PostgreSQL takes ~10 seconds to initialize

# Test connection
docker exec -it nophish-panel python3 -c "import psycopg2; print('OK')"
```

#### Issue: "SSL certificate not working"

```bash
# Check certificate files exist
ls -la ssl/

# Check nginx config
docker exec nophish-nginx nginx -t

# Regenerate certificate
sudo certbot certonly --standalone -d yourdomain.com --force-renewal
```

#### Issue: "VNC container not starting"

```bash
# Check Docker logs
docker logs cvnc-docker

# Rebuild VNC image
docker build -t cvnc-docker:latest -f CVNC-Dockerfile .

# Check resource availability
docker stats
```

---

## Maintenance

### Regular Tasks

```bash
# Update Docker images (weekly)
docker compose pull
docker compose up -d

# Clean up unused images (monthly)
docker system prune -a

# Check disk space
df -h

# View container resource usage
docker stats
```

### Backup and Restore

```bash
# Create backup
docker exec nophish-postgres pg_dump -U nophish_user nophish > backup.sql

# Restore from backup
docker exec -i nophish-postgres psql -U nophish_user nophish < backup.sql
```

---

## Uninstall

```bash
# Stop all containers
docker compose down

# Remove all containers
docker compose rm -f

# Remove volumes (WARNING: deletes all data)
docker compose down -v

# Remove images
docker rmi $(docker images -q)

# Remove project directory
cd /opt
sudo rm -rf nophish
```

---

## Support

For issues and questions:
1. Check logs: `docker compose logs -f`
2. Check [Troubleshooting](#troubleshooting) section
3. Review GitHub issues

---

<p align="center">
  <strong>Installation Complete!</strong><br>
  Access your panel at: https://yourdomain.com
</p>
