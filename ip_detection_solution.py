#!/usr/bin/env python3
"""
Cross-platform IP Detection Solution
Automatically detects the working local IP address based on OS and network interfaces.
"""

import socket
import platform
import subprocess
import re
from typing import Optional

try:
    import netifaces
    NETIFACES_AVAILABLE = True
except ImportError:
    NETIFACES_AVAILABLE = False
    print("netifaces not available, using fallback methods")

def get_os_specific_ip() -> str:
    """Return OS-specific default IP addresses"""
    system = platform.system()
    if system == 'Darwin':  # macOS
        return '192.168.254.105'
    elif system == 'Windows':
        return '192.168.254.101'
    else:
        return '127.0.0.1'

def get_ip_via_socket() -> Optional[str]:
    """Get IP by connecting to a remote address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to Google's DNS server
            s.connect(('8.8.8.8', 53))
            return s.getsockname()[0]
    except Exception:
        return None

def get_ip_via_netifaces() -> Optional[str]:
    """Get IP using netifaces library"""
    if not NETIFACES_AVAILABLE:
        return None
    
    try:
        # Find the default gateway interface
        gateways = netifaces.gateways()
        default_gateway = gateways.get('default', {})
        
        if netifaces.AF_INET in default_gateway:
            interface = default_gateway[netifaces.AF_INET][1]
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                return addrs[netifaces.AF_INET][0]['addr']
    except Exception:
        pass
    return None

def get_ip_via_system_commands() -> Optional[str]:
    """Get IP using system commands"""
    try:
        system = platform.system()
        if system == 'Darwin':  # macOS
            # Use ifconfig to get IP
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            # Look for inet addresses that aren't localhost
            matches = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
            for ip in matches:
                if not ip.startswith('127.') and not ip.startswith('169.254'):
                    return ip
        elif system == 'Windows':
            # Use ipconfig to get IP
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='utf-16')
            matches = re.findall(r'IPv4 Address[\. ]+: ([\d\.]+)', result.stdout)
            if matches:
                return matches[0]
    except Exception:
        pass
    return None

def get_working_local_ip(prefer_mac_first: bool = True) -> str:
    """
    Get the working local IP address with preference for Mac-first unless not running
    
    Args:
        prefer_mac_first: If True, prefer macOS interface when available
    
    Returns:
        str: The detected IP address
    """
    # Method 1: Try netifaces (most reliable)
    ip = get_ip_via_netifaces()
    if ip and not ip.startswith('127.'):
        print(f"Found IP via netifaces: {ip}")
        return ip
    
    # Method 2: Try system commands
    ip = get_ip_via_system_commands()
    if ip and not ip.startswith('127.'):
        print(f"Found IP via system commands: {ip}")
        return ip
    
    # Method 3: Try socket method
    ip = get_ip_via_socket()
    if ip and not ip.startswith('127.'):
        print(f"Found IP via socket method: {ip}")
        return ip
    
    # Method 4: OS-specific defaults
    ip = get_os_specific_ip()
    print(f"Using OS-specific default IP: {ip}")
    return ip

def detect_fastest_interface():
    """Detect the interface with fastest internet access"""
    # This is a simplified version - in practice you'd ping multiple endpoints
    try:
        # Test response time to common servers
        test_servers = [
            ('8.8.8.8', 'Google DNS'),
            ('1.1.1.1', 'Cloudflare DNS'),
            ('208.67.222.222', 'OpenDNS')
        ]
        
        import time
        fastest_time = float('inf')
        fastest_server = None
        
        for server, name in test_servers:
            try:
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)  # 3 second timeout
                sock.connect((server, 53))  # DNS port
                sock.close()
                end_time = time.time()
                response_time = end_time - start_time
                
                if response_time < fastest_time:
                    fastest_time = response_time
                    fastest_server = server
                    
                print(f"{name} ({server}): {response_time:.3f}s")
            except Exception:
                print(f"{name} ({server}): Timeout")
        
        if fastest_server:
            print(f"Fastest server: {fastest_server} ({fastest_time:.3f}s)")
            return fastest_server
    except Exception as e:
        print(f"Error detecting fastest interface: {e}")
    
    return None

if __name__ == "__main__":
    print("=== Cross-Platform IP Detection ===")
    print(f"Operating System: {platform.system()}")
    
    print("\n--- Detecting Fastest Internet Access ---")
    fastest = detect_fastest_interface()
    
    print("\n--- Detecting Local IP Address ---")
    ip = get_working_local_ip()
    print(f"Final detected IP: {ip}")
    
    print(f"\nRecommendation: Use {ip} as your local server address")
