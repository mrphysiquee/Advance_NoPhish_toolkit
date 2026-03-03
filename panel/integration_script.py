#!/usr/bin/env python3
"""
Integration script to run setup.sh and capture container information.
"""

import subprocess
import re
import json
import sys

def parse_setup_sh_output(output):
    """Parse setup.sh output to extract container information."""
    user_info = {}
    
    # Look for container password lines
    # Example format: [+] User 1: VNC Password: abc123... MVNC Password: def456...
    pattern = r'\[+\] User (\d+): VNC Password: ([a-f0-9]+) MVNC Password: ([a-f0-9]+)'
    matches = re.findall(pattern, output)
    
    for user_num, vnc_pass, mvnc_pass in matches:
        user_info[user_num] = {
            'vnc_password': vnc_pass,
            'mvnc_password': mvnc_pass
        }
    
    return user_info

def get_container_info():
    """Get information about all VNC containers."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}\t{{.Networks}}'],
            capture_output=True, text=True, check=True
        )
        
        containers = {}
        for line in result.stdout.strip().split('\n'):
            if line and ('vnc-user' in line or 'mvnc-user' in line):
                parts = line.split('\t')
                if len(parts) >= 2:
                    name = parts[0]
                    status = parts[1]
                    containers[name] = {
                        'name': name,
                        'status': status,
                        'ip': get_container_ip(name)
                    }
        
        return containers
    except subprocess.CalledProcessError as e:
        print(f"Error getting container info: {e}")
        return {}

def get_container_ip(container_name):
    """Get IP address of a container."""
    try:
        result = subprocess.run(
            ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', container_name],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def main():
    if len(sys.argv) < 2:
        print("Usage: python integration_script.py <setup_sh_command>")
        sys.exit(1)
    
    # Run setup.sh command
    setup_cmd = sys.argv[1]
    try:
        result = subprocess.run(setup_cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Parse output
            user_info = parse_setup_sh_output(result.stdout)
            container_info = get_container_info()
            
            # Combine information
            integration_data = {
                'user_info': user_info,
                'container_info': container_info,
                'output': result.stdout
            }
            
            # Print JSON output for Python to parse
            print(json.dumps(integration_data))
            sys.exit(0)
        else:
            print(f"Setup.sh failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()