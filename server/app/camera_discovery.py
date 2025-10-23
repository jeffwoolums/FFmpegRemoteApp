#!/usr/bin/env python3
"""
Camera Discovery Module
Discovers USB cameras and IP cameras on the network
"""

import subprocess
import json
import re
import socket
import threading
from typing import List, Dict
import time

class CameraDiscovery:
    def __init__(self):
        self.usb_cameras = []
        self.ip_cameras = []
    
    def discover_usb_cameras(self) -> List[Dict]:
        """Discover USB cameras using v4l2-ctl"""
        cameras = []
        try:
            # Get list of video devices
            result = subprocess.run(
                ['v4l2-ctl', '--list-devices'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                current_device = None
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('/dev/'):
                        # This is a device name
                        current_device = line.rstrip(':')
                    elif line.startswith('/dev/video'):
                        # This is a device path
                        device_path = line
                        # Get capabilities for this device
                        caps = self._get_device_capabilities(device_path)
                        if caps and caps.get('is_capture'):
                            cameras.append({
                                'id': device_path,
                                'name': current_device or device_path,
                                'path': device_path,
                                'type': 'usb',
                                'capabilities': caps
                            })
        except Exception as e:
            print(f"Error discovering USB cameras: {e}")
        
        self.usb_cameras = cameras
        return cameras
    
    def _get_device_capabilities(self, device_path: str) -> Dict:
        """Get capabilities for a specific video device"""
        try:
            result = subprocess.run(
                ['v4l2-ctl', '-d', device_path, '--all'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                output = result.stdout
                # Check if it's a capture device
                is_capture = 'Video Capture' in output
                
                # Get supported formats
                formats = []
                format_result = subprocess.run(
                    ['v4l2-ctl', '-d', device_path, '--list-formats-ext'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if format_result.returncode == 0:
                    current_format = None
                    for line in format_result.stdout.split('\n'):
                        if '[' in line and ']' in line:
                            # Format line
                            match = re.search(r'\[(\d+)\].*?\'(.+?)\'', line)
                            if match:
                                current_format = match.group(2)
                        elif 'Size:' in line and current_format:
                            # Resolution line
                            match = re.search(r'Size:.*?(\d+)x(\d+)', line)
                            if match:
                                formats.append({
                                    'format': current_format,
                                    'width': int(match.group(1)),
                                    'height': int(match.group(2))
                                })
                
                return {
                    'is_capture': is_capture,
                    'formats': formats[:5]  # Limit to first 5 formats
                }
        except Exception as e:
            print(f"Error getting capabilities for {device_path}: {e}")
        
        return None
    
    def scan_ip_cameras(self, subnet: str = None, timeout: int = 5) -> List[Dict]:
        """
        Scan network for IP cameras
        Simple scan looking for common RTSP and HTTP ports
        """
        cameras = []
        
        if subnet is None:
            # Get local subnet
            subnet = self._get_local_subnet()
        
        if not subnet:
            return cameras
        
        print(f"Scanning {subnet} for IP cameras...")
        
        # Common camera ports
        camera_ports = [
            (554, 'rtsp'),   # RTSP
            (8554, 'rtsp'),  # Alternative RTSP
            (80, 'http'),    # HTTP
            (8080, 'http'),  # Alternative HTTP
        ]
        
        # Parse subnet (e.g., "192.168.1.0/24")
        base_ip = '.'.join(subnet.split('.')[:3])
        
        # Scan first 10 IPs for demo (full scan would be 1-254)
        threads = []
        for i in range(1, 11):
            ip = f"{base_ip}.{i}"
            for port, protocol in camera_ports:
                t = threading.Thread(
                    target=self._check_camera_port,
                    args=(ip, port, protocol, cameras, timeout)
                )
                t.daemon = True
                t.start()
                threads.append(t)
        
        # Wait for all scans to complete
        for t in threads:
            t.join()
        
        self.ip_cameras = cameras
        return cameras
    
    def _check_camera_port(self, ip: str, port: int, protocol: str, cameras: List, timeout: int):
        """Check if a specific IP:port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                # Port is open, add as potential camera
                camera_id = f"{protocol}://{ip}:{port}"
                
                # Check if already added
                if not any(c['id'] == camera_id for c in cameras):
                    cameras.append({
                        'id': camera_id,
                        'name': f"IP Camera at {ip}:{port}",
                        'ip': ip,
                        'port': port,
                        'protocol': protocol,
                        'type': 'ip',
                        'url': self._build_camera_url(ip, port, protocol)
                    })
        except:
            pass
    
    def _build_camera_url(self, ip: str, port: int, protocol: str) -> str:
        """Build a camera URL template"""
        if protocol == 'rtsp':
            return f"rtsp://{ip}:{port}/stream"
        elif protocol == 'http':
            return f"http://{ip}:{port}/video"
        return ""
    
    def _get_local_subnet(self) -> str:
        """Get the local subnet"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Return subnet with /24
            return f"{'.'.join(local_ip.split('.')[:3])}.0/24"
        except:
            return None
    
    def test_camera_url(self, url: str, timeout: int = 5) -> bool:
        """Test if a camera URL is accessible using ffprobe"""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 
                 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                 url],
                capture_output=True,
                timeout=timeout
            )
            return result.returncode == 0
        except:
            return False
    
    def get_all_cameras(self) -> Dict:
        """Get all discovered cameras"""
        return {
            'usb': self.usb_cameras,
            'ip': self.ip_cameras
        }

if __name__ == '__main__':
    # Test the discovery
    discovery = CameraDiscovery()
    
    print("Discovering USB cameras...")
    usb = discovery.discover_usb_cameras()
    print(f"Found {len(usb)} USB camera(s)")
    for cam in usb:
        print(f"  - {cam['name']} ({cam['path']})")
    
    print("\nScanning for IP cameras...")
    ip = discovery.scan_ip_cameras()
    print(f"Found {len(ip)} potential IP camera(s)")
    for cam in ip:
        print(f"  - {cam['name']} ({cam['url']})")
    
    print("\nAll cameras:")
    print(json.dumps(discovery.get_all_cameras(), indent=2))
