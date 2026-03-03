#!/usr/bin/env python3
"""
Simple test script to create a campaign through the panel.
"""

import requests
import json

# Panel configuration
PANEL_URL = "http://localhost:5000"
LOGIN_URL = f"{PANEL_URL}/login"
DASHBOARD_URL = f"{PANEL_URL}/dashboard"

# Test credentials
USERNAME = "angler"
PASSWORD = "angler"  # Default password from config

def test_panel():
    """Test panel functionality."""
    print("Testing NoPhish Panel...")
    
    # Step 1: Login
    print("1. Testing login...")
    session = requests.Session()
    
    # Get login page for CSRF token
    response = session.get(LOGIN_URL)
    if response.status_code != 200:
        print(f"Failed to get login page: {response.status_code}")
        return False
    
    # Extract CSRF token (if present)
    csrf_token = None
    if 'csrf_token' in response.text:
        # Simple extraction - in real implementation you'd need proper HTML parsing
        import re
        csrf_match = re.search(r'name="csrf_token"\s*value="([^"]*)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
    
    # Login
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
    if response.status_code != 200 or "login" in response.url.lower():
        print(f"Login failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return False
    
    print("✓ Login successful")
    
    # Step 2: Create campaign
    print("2. Creating test campaign...")
    campaign_data = {
        "name": "Test Campaign",
        "domain": "test-phishing.com",
        "target": "https://google.com",
        "num_users": 1,
        "ssl": False,
        "cert_path": "",
        "key_path": "",
        "useragent": "",
        "custom_param": "",
        "export_format": "default",
        "redirect": False,
        "zip_profile": True
    }
    
    response = session.post(f"{PANEL_URL}/campaigns/create", data=campaign_data)
    if response.status_code != 200:
        print(f"Failed to create campaign: {response.status_code}")
        return False
    
    print("✓ Campaign created successfully")
    
    # Step 3: Check dashboard
    print("3. Checking dashboard...")
    response = session.get(DASHBOARD_URL)
    if response.status_code != 200:
        print(f"Failed to access dashboard: {response.status_code}")
        return False
    
    print("✓ Dashboard accessible")
    
    print("\n🎉 All tests passed! Panel is working correctly.")
    return True

if __name__ == "__main__":
    test_panel()