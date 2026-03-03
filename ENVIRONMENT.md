# Environment Configuration Guide

Complete reference for all environment variables in NoPhish.

---

## Overview

NoPhish uses environment variables for configuration. All configuration is managed through:
- `.env` file (local development)
- Environment variables (production)

---

## Required Variables

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | nophish | Database name |
| `POSTGRES_USER` | nophish_user | Database username |
| `POSTGRES_PASSWORD` | - | **REQUIRED** Database password |

```env
# Example
POSTGRES_DB=nophish
POSTGRES_USER=nophish_user
POSTGRES_PASSWORD=your_very_secure_password_123!
```

---

### Security Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | - | **REQUIRED** Flask secret key |
| `JWT_SECRET_KEY` | ${SECRET_KEY} | JWT signing key |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Token expiration time |

```env
# Generate secure key
# Run: python3 -c "import secrets; print(secrets.token_hex(32))"

SECRET_KEY=your_generated_secret_key_here
JWT_SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

### Domain Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PANEL_DOMAIN` | - | **REQUIRED** Your domain |
| `CORS_ORIGINS` | - | Allowed CORS origins |

```env
# Example
PANEL_DOMAIN=yourdomain.com
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
```

---

## Optional Variables

### Telegram Notifications

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token |
| `TELEGRAM_CHAT_ID` | - | Telegram chat ID |

```env
# Get token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHOT_ID=123456789
```

---

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | redis://redis:6379 | Redis connection URL |

```env
REDIS_URL=redis://redis:6379
```

---

### Flask Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | production | Flask environment |
| `FLASK_DEBUG` | 0 | Debug mode |

```env
FLASK_ENV=production
FLASK_DEBUG=0
```

---

### Complete Example .env

```env
# ==========================================
# NoPhish Environment Configuration
# ==========================================

# ====================
# DATABASE
# ====================
POSTGRES_DB=nophish
POSTGRES_USER=nophish_user
POSTGRES_PASSWORD=change_this_to_a_very_secure_password_123!

# ====================
# SECURITY
# ====================
SECRET_KEY=generate_with_python_secrets_token_hex_32
JWT_SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ====================
# DOMAIN
# ====================
PANEL_DOMAIN=yourdomain.com
CORS_ORIGINS=["https://yourdomain.com"]

# ====================
# TELEGRAM (Optional)
# ====================
# TELEGRAM_BOT_TOKEN=
# TELEGRAM_CHAT_ID=

# ====================
# REDIS
# ====================
REDIS_URL=redis://redis:6379

# ====================
# FLASK
# ====================
FLASK_ENV=production
FLASK_DEBUG=0
```

---

## Generating Secrets

### Generate SECRET_KEY

```bash
# Python 3
python3 -c "import secrets; print(secrets.token_hex(32))"

# Output example:
# a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2
```

### Generate JWT_SECRET_KEY

```bash
# Use a different key for JWT
python3 -c "import secrets; print(secrets.token_hex(32))"

# Output example:
# z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z9y8x7w6
```

---

## Security Best Practices

### 1. Use Strong Passwords

```bash
# Generate secure database password
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 2. Never Commit Secrets

```
# .gitignore must contain:
.env
*.pem
*.key
```

### 3. Use Different Keys for Different Environments

```env
# Production
SECRET_KEY=production_secret_key_different_from_dev

# Development
SECRET_KEY=dev_secret_key
```

### 4. Rotate Secrets Regularly

```bash
# Generate new keys
python3 -c "import secrets; print(secrets.token_hex(32))"

# Update .env file
# Restart containers
docker compose down
docker compose up -d
```

---

## Docker Compose Usage

### Development

```bash
# Uses default docker-compose.yml
docker compose up -d
```

### Production

```bash
# Uses docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

### Override Configuration

```bash
# Create docker-compose.override.yml for local changes
# This file is automatically merged with docker-compose.yml
# NOTE: Add to .gitignore to prevent accidental commits
```

---

## Container Resource Limits

| Service | Memory | CPU |
|---------|--------|-----|
| postgres | 512MB | 0.5 |
| redis | 256MB | 0.25 |
| panel | 1GB | 1.0 |
| nginx | 256MB | 0.5 |

Adjust in `docker-compose.prod.yml` as needed.

---

## Troubleshooting

### Database Connection Error

```bash
# Verify database credentials
cat .env | grep POSTGRES

# Check if database is running
docker compose ps postgres

# View database logs
docker compose logs postgres
```

### Invalid SECRET_KEY

```bash
# Generate new key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Update .env
nano .env

# Restart services
docker compose restart panel
```

### CORS Errors

```bash
# Update CORS_ORIGINS in .env
CORS_ORIGINS=["https://yourdomain.com"]

# Restart panel
docker compose restart panel
```

---

## Environment Variables Summary

| Variable | Required | Default |
|----------|----------|---------|
| POSTGRES_DB | No | nophish |
| POSTGRES_USER | No | nophish_user |
| POSTGRES_PASSWORD | **Yes** | - |
| SECRET_KEY | **Yes** | - |
| JWT_SECRET_KEY | No | ${SECRET_KEY} |
| ALGORITHM | No | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | No | 30 |
| PANEL_DOMAIN | **Yes** | - |
| CORS_ORIGINS | No | [] |
| TELEGRAM_BOT_TOKEN | No | - |
| TELEGRAM_CHAT_ID | No | - |
| REDIS_URL | No | redis://redis:6379 |
| FLASK_ENV | No | production |
