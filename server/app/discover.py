#!/usr/bin/env python3
"""
Stream Control Discovery Tool

This tool finds Stream Control services on your local network.
Run this on any computer on the same network as your Raspberry Pi.

Usage: python3 discover.py
"""

import socket
import time
import sys

DISCOVERY_PORT = 48888
DISCOVERY_MESSAGE = b'STREAM_CONTROL_DISCOVERY'
TIMEOUT = 5

def discover_services():
    """Discover Stream Control services on the network"""
    print("Searching for Stream Control services on the network...")
    print(f"Broadcasting on port {DISCOVERY_PORT}...")
    print("-" * 60)
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(TIMEOUT)
    
    # Send broadcast
    try:
        sock.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))
        print(f"Broadcast sent, waiting {TIMEOUT} seconds for responses...\n")
    except Exception as e:
        print(f"Error sending broadcast: {e}")
        return []
    
    # Collect responses
    services = []
    start_time = time.time()
    
    while time.time() - start_time < TIMEOUT:
        try:
            data, addr = sock.recvfrom(1024)
            response = data.decode()
            
            if response.startswith('STREAM_CONTROL_RESPONSE|'):
                parts = response.split('|')
                if len(parts) >= 4:
                    _, hostname, ip, port = parts[:4]
                    service = {
                        'hostname': hostname,
                        'ip': ip,
                        'port': port,
                        'url': f"http://{ip}:{port}",
                        'mdns_url': f"http://{hostname}.local:{port}"
                    }
                    
                    # Avoid duplicates
                    if service not in services:
                        services.append(service)
                        print(f"✓ Found: {hostname}")
                        print(f"  IP Address:   {ip}")
                        print(f"  Web URL:      {service['url']}")
                        print(f"  mDNS URL:     {service['mdns_url']}")
                        print()
        except socket.timeout:
            continue
        except Exception as e:
            continue
    
    sock.close()
    return services

def main():
    print("\n" + "=" * 60)
    print("Stream Control Discovery Tool")
    print("=" * 60 + "\n")
    
    services = discover_services()
    
    print("-" * 60)
    if services:
        print(f"\nFound {len(services)} service(s)!")
        print("\nYou can access the Stream Control interface at:")
        for i, service in enumerate(services, 1):
            print(f"\n{i}. {service['hostname']}")
            print(f"   {service['url']}")
            if service['hostname'] != 'localhost':
                print(f"   {service['mdns_url']}")
    else:
        print("\nNo Stream Control services found on the network.")
        print("\nTroubleshooting:")
        print("1. Make sure the Raspberry Pi is on the same network")
        print("2. Check if the stream-control service is running:")
        print("   ssh jeff@<raspberry-pi-ip> 'systemctl status stream-control'")
        print("3. Check your firewall settings")
    
    print("\n" + "=" * 60 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiscovery cancelled.")
        sys.exit(0)
