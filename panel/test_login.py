#!/usr/bin/env python3
import requests
import re

# Test the complete login flow
session = requests.Session()

# Get login page for CSRF token
response = session.get('https://account-login.help/panel/login')
print(f"Login page status: {response.status_code}")

# Extract CSRF token if present
csrf_token = None
csrf_match = re.search(r'name="csrf_token"\s*value="([^"]*)"', response.text)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print(f"Found CSRF token: {csrf_token}")

# Login data
login_data = {
    "username": "angler",
    "password": "angler"
    # "csrf_token": csrf_token if csrf_token else ""
}

# Perform login
response = session.post('https://account-login.help/panel/login', data=login_data, allow_redirects=True)
print(f"Login response status: {response.status_code}")
print(f"Final URL: {response.url}")

# Test dashboard access
dashboard_response = session.get('https://account-login.help/panel/dashboard')
print(f"Dashboard status: {dashboard_response.status_code}")
print(f"Dashboard title: {dashboard_response.text[:100]}")

if "dashboard" in dashboard_response.url.lower():
    print("✅ Login successful!")
else:
    print("❌ Login failed")