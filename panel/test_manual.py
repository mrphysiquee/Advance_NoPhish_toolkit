#!/usr/bin/env python3
"""
Simple test script to manually test the panel.
"""

import requests

PANEL_URL = "http://localhost:5000"

def test_manual():
    print("NoPhish Panel Manual Test")
    print("=" * 30)
    
    print(f"\n1. Testing panel accessibility...")
    try:
        response = requests.get(f"{PANEL_URL}/")
        if response.status_code == 200:
            print("✓ Panel is accessible")
        else:
            print(f"✗ Panel returned status: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return
    
    print(f"\n2. Testing login page...")
    try:
        response = requests.get(f"{PANEL_URL}/login")
        if response.status_code == 200:
            print("✓ Login page accessible")
        else:
            print(f"✗ Login page returned status: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to get login page: {e}")
    
    print(f"\n3. Testing dashboard (should redirect to login)...")
    try:
        response = requests.get(f"{PANEL_URL}/dashboard")
        if response.status_code == 302:
            print("✓ Dashboard properly redirects to login")
        else:
            print(f"Dashboard returned status: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to test dashboard: {e}")
    
    print(f"\n4. Testing campaigns page...")
    try:
        response = requests.get(f"{PANEL_URL}/campaigns")
        if response.status_code == 302:
            print("✓ Campaigns page properly redirects to login")
        else:
            print(f"Campaigns page returned status: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to test campaigns page: {e}")
    
    print("\n" + "=" * 30)
    print("Manual Test Complete!")
    print("\nTo test campaign creation:")
    print("1. Open browser to: http://localhost:5000/login")
    print("2. Login with:angler/angler")
    print("3. Navigate to Campaigns -> Create Campaign")
    print("4. Fill form and submit to test integration")

if __name__ == "__main__":
    test_manual()