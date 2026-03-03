#!/bin/bash

# NoPhish Panel Recovery Script
# Usage: ./restore_nophish.sh <backup_file>

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -lh /var/backups/nophish/nophish_backup_*.tar.gz
    exit 1
fi

BACKUP_FILE="$1"
BACKUP_DIR="/var/backups/nophish"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/nophish_backup_*.tar.gz
    exit 1
fi

echo "[+] Starting NoPhish restore from: $BACKUP_FILE"
echo "WARNING: This will stop services and overwrite current data!"
read -p "Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 1
fi

# Stop services
echo "[-] Stopping services..."
systemctl stop nophish-panel
systemctl stop nginx

# Extract backup
echo "[-] Extracting backup..."
cd "$BACKUP_DIR"
tar -xzf "$BACKUP_FILE"

# Get backup name (remove .tar.gz extension)
BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)

# Restore database
echo "[-] Restoring database..."
cp "${BACKUP_NAME}_panel.db" /root/NoPhish/output/panel.db

# Restore configuration
echo "[-] Restoring configuration..."
cp -r "${BACKUP_NAME}_panel_config"/* /root/NoPhish/panel/

# Restore output directory
echo "[-] Restoring output directory..."
rm -rf /root/NoPhish/output/*
cp -r "${BACKUP_NAME}_output"/* /root/NoPhish/output/

# Restore nginx configuration
echo "[-] Restoring nginx configuration..."
cp "${BACKUP_NAME}_nginx_config" /etc/nginx/sites-enabled/account-login.help

# Restore SSL certificates
echo "[-] Restoring SSL certificates..."
rm -rf /etc/letsencrypt/live/account-login.help
cp -r "${BACKUP_NAME}_ssl_certs" /etc/letsencrypt/live/account-login.help

# Clean up extracted files
rm -rf "${BACKUP_NAME}_panel.db" "${BACKUP_NAME}_panel_config" "${BACKUP_NAME}_output" "${BACKUP_NAME}_nginx_config" "${BACKUP_NAME}_ssl_certs"

# Start services
echo "[-] Starting services..."
systemctl start nginx
systemctl start nophish-panel

echo "[+] Restore completed successfully!"
echo "Panel should be available at: https://account-login.help/panel/"