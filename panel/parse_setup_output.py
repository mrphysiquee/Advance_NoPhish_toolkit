#!/usr/bin/env python3
"""
Parse setup.sh output and extract campaign information.
"""

import re
import json

def parse_setup_sh_output(output):
    """Parse setup.sh output to extract campaign information."""
    user_info = {}
    admin_password = None
    
    # Extract container passwords from output
    # Example format: [+] User 1: VNC Password: abc123... MVNC Password: def456...
    password_pattern = r'\[+\] User (\d+): VNC Password: ([a-f0-9]+) MVNC Password: ([a-f0-9]+)'
    matches = re.findall(password_pattern, output)
    
    for user_num, vnc_pass, mvnc_pass in matches:
        user_info[user_num] = {
            'vnc_password': vnc_pass,
            'mvnc_password': mvnc_pass
        }
    
# Extract admin password - clean the output first
    clean_output = output.replace('\x1b[0K', '').replace('\x1b[7A', '')
    
    # Look for password line
    admin_pattern = r'Password:\s*([a-f0-9A-F]+)'
    admin_match = re.search(admin_pattern, clean_output)
    if admin_match:
        admin_password = admin_match.group(1)
    
    # Try more flexible pattern if needed
    if not admin_password:
        admin_pattern = r'Password:\s*([a-f0-9A-F]+)'
        admin_match = re.search(admin_pattern, output)
        if admin_match:
            admin_password = admin_match.group(1)
    
    return {
        'user_info': user_info,
        'admin_password': admin_password
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python parse_setup_output.py '<setup_sh_output>'")
        sys.exit(1)
    
    output = sys.argv[1]
    result = parse_setup_sh_output(output)
    print(json.dumps(result))