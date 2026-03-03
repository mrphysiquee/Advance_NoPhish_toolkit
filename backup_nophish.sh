#!/bin/bash

# NoPhish Panel Backup Script
# Usage: ./backup_nophish.sh [backup_name]

BACKUP_DIR="/var/backups/nophish"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-nophish_backup_$DATE}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "[+] Starting NoPhish backup: $BACKUP_NAME"

# Backup database
echo "[-] Backing up database..."
cp /root/NoPhish/output/panel.db "$BACKUP_DIR/${BACKUP_NAME}_panel.db"

# Backup configuration
echo "[-] Backing up configuration..."
cp -r /root/NoPhish/panel "$BACKUP_DIR/${BACKUP_NAME}_panel_config"

# Backup domains
echo "[-] Backing up domains..."
cp -r /root/NoPhish/output "$BACKUP_DIR/${BACKUP_NAME}_output"

# Backup nginx configuration
echo "[-] Backing up nginx configuration..."
cp /etc/nginx/sites-enabled/account-login.help "$BACKUP_DIR/${BACKUP_NAME}_nginx_config"

# Backup SSL certificates
echo "[-] Backing up SSL certificates..."
cp -r /etc/letsencrypt/live/account-login.help "$BACKUP_DIR/${BACKUP_NAME}_ssl_certs"

# Create backup archive
echo "[-] Creating backup archive..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}_panel.db" "${BACKUP_NAME}_panel_config" "${BACKUP_NAME}_output" "${BACKUP_NAME}_nginx_config" "${BACKUP_NAME}_ssl_certs"

# Clean up temporary files
rm -rf "${BACKUP_NAME}_panel.db" "${BACKUP_NAME}_panel_config" "${BACKUP_NAME}_output" "${BACKUP_NAME}_nginx_config" "${BACKUP_NAME}_ssl_certs"

# Calculate backup size
BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)

echo "[+] Backup completed successfully!"
echo "Backup file: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "Backup size: $BACKUP_SIZE"

# List recent backups
echo ""
echo "Recent backups:"
ls -lh "$BACKUP_DIR"/nophish_backup_*.tar.gz | tail -5