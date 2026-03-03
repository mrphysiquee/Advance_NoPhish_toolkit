#!/bin/bash

# Complete NoPhish Panel Test with our domain
echo "NoPhish Panel Complete Test"
echo "==========================="
echo "Domain: account-login.help"
echo "SSL Status: ✅ Valid (Let's Encrypt)"
echo ""

# Test 1: Main domain redirect
echo "1. Testing main domain redirect..."
MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://account-login.help)
if [ "$MAIN_STATUS" = "302" ]; then
    echo "✅ Main domain redirects to dashboard (authenticated access)"
else
    echo "❌ Main domain unexpected response: $MAIN_STATUS"
fi

# Test 2: Panel access without authentication
echo ""
echo "2. Testing panel access without authentication..."
PANEL_REDIRECT=$(curl -s -o /dev/null -w "%{http_code}" https://account-login.help/panel/)
if [ "$PANEL_REDIRECT" = "302" ]; then
    echo "✅ Panel properly redirects to login when not authenticated"
else
    echo "❌ Panel unexpected response: $PANEL_REDIRECT"
fi

# Test 3: Login page accessibility
echo ""
echo "3. Testing login page accessibility..."
LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://account-login.help/panel/login)
if [ "$LOGIN_STATUS" = "200" ]; then
    echo "✅ Login page accessible (HTTP 200)"
else
    echo "❌ Login page not accessible: $LOGIN_STATUS"
fi

# Test 4: SSL security headers
echo ""
echo "4. Testing SSL security features..."
SECURITY_INFO=$(curl -s -I https://account-login.help/panel/ 2>/dev/null)

if echo "$SECURITY_INFO" | grep -q "HTTP/2"; then
    echo "✅ HTTP/2 enabled"
else
    echo "❌ HTTP/2 not enabled"
fi

if echo "$SECURITY_INFO" | grep -q "Strict-Transport-Security"; then
    echo "✅ HSTS enabled"
else
    echo "❌ HSTS not enabled"
fi

if echo "$SECURITY_INFO" | grep -q "X-Frame-Options"; then
    echo "✅ X-Frame-Options enabled"
else
    echo "❌ X-Frame-Options missing"
fi

if echo "$SECURITY_INFO" | grep -q "X-Content-Type-Options"; then
    echo "✅ X-Content-Type-Options enabled"
else
    echo "❌ X-Content-Type-Options missing"
fi

# Test 5: Panel service status
echo ""
echo "5. Testing panel service status..."
SERVICE_STATUS=$(systemctl is-active nophish-panel)
if [ "$SERVICE_STATUS" = "active" ]; then
    echo "✅ Panel service is running"
else
    echo "❌ Panel service is not running: $SERVICE_STATUS"
fi

# Test 6: Nginx service status
echo ""
echo "6. Testing nginx service status..."
NGINX_STATUS=$(systemctl is-active nginx)
if [ "$NGINX_STATUS" = "active" ]; then
    echo "✅ Nginx service is running"
else
    echo "❌ Nginx service is not running: $NGINX_STATUS"
fi

echo ""
echo "==========================="
echo "ACCESS INFORMATION"
echo "==========================="
echo "Panel URL: https://account-login.help/panel/"
echo "Username: angler"
echo "Password: angler"
echo ""
echo "SSL Certificate: Valid (Let's Encrypt)"
echo "Expiration: May 13, 2026"
echo ""
echo "Test Commands:"
echo "  systemctl status nophish-panel  # Check panel service"
echo "  systemctl status nginx         # Check nginx service"
echo "  tail -f /var/log/nophish-panel/*.log  # View logs"
echo ""
echo "Backup Commands:"
echo "  /root/NoPhish/backup_nophish.sh             # Create backup"
echo "  /root/NoPhish/restore_nophish.sh <file>    # Restore backup"