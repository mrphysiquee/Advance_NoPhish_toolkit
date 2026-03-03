# NoPhish - Advanced Phishing Simulation Platform

<p align="center">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=white" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="Nginx">
</p>

A professional-grade, containerized phishing simulation and security assessment platform built with Chrome/noVNC, React admin panel, Flask backend, PostgreSQL database, Redis caching, and Nginx reverse proxy.

---

## ⚠️ Legal Disclaimer

**FOR EDUCATIONAL AND AUTHORIZED SECURITY TESTING PURPOSES ONLY**

This tool is intended for:
- Security professionals conducting authorized penetration tests
- Organizations testing their employees' security awareness
- Educational purposes in cybersecurity courses
- Red team operations with explicit written consent

**Unauthorized use against systems you do not own or have explicit permission to test is illegal and strictly prohibited.**

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [License](#license)

---

## ✨ Features

### Core Features
- **noVNC Integration** - Browser-based VNC client with full keyboard/mouse support
- **Mobile Support** - Optimized mobile VNC interface with virtual keyboard
- **Chrome/Firefox Browsers** - Pre-configured browser containers for phishing simulation
- **Real-time Monitoring** - Live session tracking and data collection
- **Campaign Management** - Create, manage, and track phishing campaigns
- **JWT Authentication** - Secure API authentication with token-based access
- **Telegram Notifications** - Real-time alerts via Telegram bot

### Admin Panel
- Dashboard with campaign statistics
- Campaign creation and management
- Collected data visualization
- User management
- Container monitoring

### Technical Features
- Docker containerization
- Redis session management
- PostgreSQL database
- Nginx reverse proxy with SSL
- Auto-scaling VNC containers
- Mobile-optimized viewport

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Internet                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy (443/80)                     │
│                  (nophish-nginx container)                           │
│                                                                          │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐               │
│   │  /api/*     │  │  /vnc/<id>/* │  │  /           │               │
│   │  → Backend  │  │  → VNC       │  │  → React UI │               │
│   └─────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
          ┌────────────┐   ┌────────────┐   ┌────────────┐
          │   Panel    │   │   VNC      │   │  Frontend  │
          │  (Flask)   │   │ Containers │   │  (React)   │
          │  :5000     │   │  :6901     │   │   Static   │
          └────────────┘   └────────────┘   └────────────┘
                    │               │               
                    └───────────────┼───────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          ┌────────────┐   ┌────────────┐   ┌────────────┐
          │ PostgreSQL │   │   Redis   │   │  Chrome    │
          │   :5432    │   │   :6379   │   │  Browser   │
          └────────────┘   └────────────┘   └────────────┘
```

### Components

| Component | Container | Port | Technology |
|-----------|-----------|------|------------|
| Reverse Proxy | nophish-nginx | 80, 443 | Nginx |
| Admin Panel | nophish-panel | 5000 | Flask + Gunicorn |
| Frontend UI | nophish-frontend | 8080 | React + Nginx |
| Database | nophish-postgres | 5432 | PostgreSQL 15 |
| Cache | nophish-redis | 6379 | Redis 7 |
| VNC Sessions | vnc-* | 6901 | noVNC + Chrome |

---

## 🔧 Prerequisites

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 20 GB | 50+ GB SSD |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

### Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git nginx certbot python3 python3-pip docker.io docker-compose

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
```

### Network Requirements

| Port | Service | Description |
|------|---------|-------------|
| 80 | HTTP | Let's Encrypt verification |
| 443 | HTTPS | Main access |
| 22 | SSH | Server management |

### Domain Requirements

- Registered domain name
- DNS A record pointing to server IP
- For SSL: ports 80/443 must be accessible

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/NoPhish.git
cd NoPhish
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

### 3. SSL Certificate Setup

```bash
# Generate Let's Encrypt certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to project
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
sudo chmod 644 ./ssl/*.pem
```

### 4. Start Services

```bash
# Build and start all containers
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5. Access the Panel

```
URL: https://yourdomain.com
Username: admin
Password: changeme123
```

---

## 📖 Installation

### Step 1: Server Preparation

```bash
# Create project directory
sudo mkdir -p /opt/nophish
cd /opt/nophish

# Clone repository
sudo git clone https://github.com/your-username/NoPhish.git .

# Set ownership
sudo chown -R $USER:$USER /opt/nophish
```

### Step 2: Environment Configuration

Create `.env` file:

```env
# ====================
# Database Configuration
# ====================
POSTGRES_PASSWORD=your_very_secure_password_here
POSTGRES_DB=nophish
POSTGRES_USER=nophish_user

# ====================
# Security Configuration
# ====================
SECRET_KEY=your_secret_key_minimum_32_characters_long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ====================
# Domain Configuration
# ====================
PANEL_DOMAIN=yourdomain.com
CORS_ORIGINS=["https://yourdomain.com", "http://localhost:3000"]

# ====================
# Telegram Notifications (Optional)
# ====================
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# ====================
# Redis Configuration
# ====================
REDIS_URL=redis://redis:6379
```

### Step 3: SSL Certificate

#### Option A: Let's Encrypt (Free)

```bash
# Stop any service using port 80
sudo systemctl stop nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chmod 644 ssl/*.pem
```

#### Option B: Purchased Certificate

```bash
# Place your certificates in ssl/ directory
# Rename them to:
#   fullchain.pem  (certificate + intermediate)
#   privkey.pem    (private key)
```

### Step 4: Build & Deploy

```bash
# Build all Docker images
docker compose build

# Start all services
docker compose up -d

# Check container status
docker compose ps

# View logs
docker compose logs -f panel
```

### Step 5: Initial Setup

```bash
# Create admin user (first login)
# Access: https://yourdomain.com
# Default credentials after first run:
# Username: admin
# Password: changeme123

# Change password immediately after first login!
```

---

## ⚙️ Configuration

### Nginx Configuration

The main nginx configuration is in `nginx/nginx.conf`. Key settings:

```nginx
# VNC Proxy - forwards to noVNC containers
location ~ ^/vnc/([^/]+)/(.+)$ {
    resolver 127.0.0.11 valid=30s;
    set $vnc_container $1;
    set $vnc_path $2;
    proxy_pass http://$vnc_container:6901/$vnc_path;
    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

# API routes
location /api/ {
    proxy_pass http://panel:5000;
}
```

### VNC Container Configuration

Available VNC Dockerfiles:

| File | Browser | Display | Use Case |
|------|---------|---------|----------|
| `VNC-Dockerfile` | Firefox | Desktop | Standard desktop simulation |
| `CVNC-Dockerfile` | Chrome | Desktop | Chrome desktop testing |
| `MVNC-Dockerfile` | Firefox | Mobile | Mobile browser simulation |
| `CMVNC-Dockerfile` | Chrome | Mobile | Mobile Chrome testing |

### Mobile VNC Features

The mobile VNC interface (`vnc/mconn.html`) includes:
- Optimized viewport meta tags
- Touch gesture support
- Virtual keyboard toggle
- Landscape/portrait adaptation
- iOS Safari / Android Chrome support

---

## 📡 API Documentation

### Authentication

All API requests require JWT token in Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://yourdomain.com/api/campaigns
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/logout` | User logout |
| GET | `/api/campaigns` | List campaigns |
| POST | `/api/campaigns` | Create campaign |
| GET | `/api/campaigns/<id>` | Campaign details |
| DELETE | `/api/campaigns/<id>` | Delete campaign |
| GET | `/api/collected` | Collected data |
| POST | `/api/vnc/start` | Start VNC session |
| POST | `/api/vnc/stop` | Stop VNC session |

### Campaign Payload Example

```json
{
  "name": "Google Phishing Test",
  "target_url": "https://accounts.google.com",
  "template": "google_login",
  "browser": "chrome",
  "mobile": false,
  "redirect_url": "https://www.google.com"
}
```

---

## 🔧 Usage

### Creating a Campaign

1. Login to admin panel
2. Click "New Campaign"
3. Fill in campaign details:
   - Campaign name
   - Target URL (phishing destination)
   - Browser type (Chrome/Firefox)
   - Device type (Desktop/Mobile)
   - Redirect URL (after data capture)
4. Click "Create"
5. Share generated phishing URL

### Monitoring Campaigns

```bash
# View active containers
docker ps --filter "name=vnc-"

# View real-time logs
docker logs -f vnc-session-id

# Check collected data
docker exec -it nophish-panel ls -la collected/
```

### Stopping a Campaign

```bash
# Stop all VNC containers
docker stop $(docker ps -aq --filter "name=vnc-")

# Or stop specific container
docker stop vnc-session-id
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. SSL Certificate Not Working

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Check nginx logs
docker logs nophish-nginx
```

#### 2. VNC Connection Failed

```bash
# Check VNC container status
docker ps -a | grep vnc

# View VNC logs
docker logs <container-name>

# Check if port is exposed
docker port <container-name>
```

#### 3. Database Connection Error

```bash
# Check PostgreSQL logs
docker logs nophish-postgres

# Test connection
docker exec -it nophish-panel psql -U nophish_user -d nophish
```

#### 4. Frontend Not Loading

```bash
# Rebuild frontend
docker compose build frontend
docker compose up -d frontend

# Check nginx config
docker exec -it nophish-nginx nginx -t
```

### Health Checks

```bash
# Check all services
curl -f https://yourdomain.com/api/health || echo "API Unhealthy"

# Check database
docker exec nophish-postgres pg_isready -U nophish_user

# Check Redis
docker exec nophish-redis redis-cli ping
```

---

## 🔐 Security

### Recommended Security Practices

1. **Change Default Credentials**
   ```bash
   # Update admin password immediately after first login
   ```

2. **Use Strong Secrets**
   ```bash
   # Generate strong SECRET_KEY
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Enable Firewall**
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

4. **Regular Updates**
   ```bash
   # Update Docker images regularly
   docker compose pull
   docker compose up -d
   ```

5. **Monitor Logs**
   ```bash
   # Set up log monitoring
   docker compose logs --tail=100 > /var/log/nophish.log
   ```

### SSL/TLS Configuration

The nginx configuration uses:
- TLS 1.2 and 1.3 only
- Strong ciphers (HIGH:!aNULL:!MD5)
- HTTP/2 support
- OCSP stapling (production)

---

## 📁 Project Structure

```
NoPhish/
├── panel/                    # Flask Admin Panel
│   ├── app/
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── docker_manager.py  # VNC container management
│   │   ├── collector.py     # Data collection
│   │   └── routes/         # API routes
│   ├── requirements.txt    # Python dependencies
│   ├── gunicorn.conf.py    # WSGI config
│   └── wsgi.py            # Application entry
│
├── vnc/                     # noVNC Interface
│   ├── mconn.html         # Mobile VNC page
│   ├── conn.html          # Desktop VNC page
│   ├── ui.js             # noVNC UI
│   ├── base.css          # Styles
│   └── keyboard.svg      # Virtual keyboard
│
├── nginx/                   # Nginx Config
│   └── nginx.conf         # Reverse proxy config
│
├── frontend/               # React Admin UI
│   ├── src/               # React source
│   ├── public/            # Static assets
│   ├── package.json      # Node dependencies
│   └── Dockerfile        # Frontend container
│
├── database/               # Database
│   └── init.sql          # Schema initialization
│
├── ssl/                    # SSL Certificates
│   ├── fullchain.pem     # SSL certificate
│   └── privkey.pem       # Private key
│
├── docker-compose.yml      # Main orchestration
├── PANEL-Dockerfile       # Flask container
├── NGINX-Dockerfile       # Nginx container
├── CVNC-Dockerfile       # Chrome Desktop VNC
├── CMVNC-Dockerfile      # Chrome Mobile VNC
├── MVNC-Dockerfile       # Firefox Mobile VNC
├── .env.example          # Environment template
└── .gitignore           # Git ignore rules
```

---

## 🐳 Docker Commands

### Common Operations

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Restart specific service
docker compose restart panel

# Rebuild service
docker compose build panel
docker compose up -d panel

# Access container shell
docker exec -it nophish-panel /bin/bash

# View resource usage
docker stats

# Clean up unused resources
docker system prune -a
```

### Scaling VNC Containers

```bash
# Start multiple VNC containers
for i in {1..5}; do
  docker run -d --name vnc-session-$i cvnc-docker:latest
done

# Or use the API endpoint
curl -X POST https://yourdomain.com/api/vnc/start \
  -H "Authorization: Bearer TOKEN" \
  -d '{"browser": "chrome", "mobile": false}'
```

---

## 📄 License

This project is provided for educational and authorized security testing purposes only.

See [LICENSE](LICENSE) for full details.

---

## ⚡ Quick Reference

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start all services |
| `docker compose down` | Stop all services |
| `docker compose logs -f` | View logs |
| `docker compose restart` | Restart services |
| `docker exec -it panel bash` | Access panel shell |
| `certbot renew` | Renew SSL certificate |

### Access URLs

| Service | URL |
|---------|-----|
| Admin Panel | https://yourdomain.com |
| API | https://yourdomain.com/api |
| VNC Demo | https://yourdomain.com/vnc/demo/conn.html |
| Mobile VNC | https://yourdomain.com/vnc/demo/mconn.html |

---

<p align="center">
  <strong>NoPhish - Advanced Phishing Simulation Platform</strong><br>
  Built with ❤️ for security professionals
</p>
