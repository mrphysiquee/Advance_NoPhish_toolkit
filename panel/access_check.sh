#!/bin/bash

# Quick access check for NoPhish Panel
echo "NoPhish Panel Access Check"
echo "========================="

echo "1. Testing panel accessibility..."
if curl -s -o /dev/null -w "%{http_code}" https://account-login.help/panel/ | grep -q "302"; then
    echo "✅ Panel redirects to login (correct)"
else
    echo "❌ Panel not responding correctly"
fi

echo ""
echo "2. Testing login page..."
if curl -s -o /dev/null -w "%{http_code}" https://account-login.help/panel/login | grep -q "200"; then
    echo "✅ Login page accessible"
else
    echo "❌ Login page not accessible"
fi

echo ""
echo "3. Testing HTTPS security..."
if curl -s -I https://account-login.help/panel/ | grep -q "HTTP/2"; then
    echo "✅ HTTP/2 enabled"
else
    echo "❌ HTTP/2 not working"
fi

echo ""
echo "4. Testing security headers..."
SECURITY_HEADERS=$(curl -s -I https://account-login.help/panel/ | grep -i "content-security-policy\|x-frame-options\|x-content-type-options")
if echo "$SECURITY_HEADERS" | grep -q "Content-Security-Policy"; then
    echo "✅ Content Security Policy enabled"
else
    echo "❌ Content Security Policy missing"
fi

echo ""
echo "Login Credentials:"
echo "Username: angler"
echo "Password: angler"
echo ""
echo "Panel URL: https://account-login.help/panel/"