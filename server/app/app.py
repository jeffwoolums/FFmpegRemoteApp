#!/usr/bin/env python3
import os
import json
import subprocess
import signal
import socket
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path

app = Flask(__name__)
CONFIG_FILE = Path.home() / 'stream-control' / 'config.json'
PID_FILE = Path.home() / 'stream-control' / 'stream.pid'

# Discovery settings
DISCOVERY_PORT = 48888
DISCOVERY_MESSAGE = b'STREAM_CONTROL_DISCOVERY'

# Default configuration
DEFAULT_CONFIG = {
    'platforms': {
        'youtube': {
            'name': 'YouTube',
            'rtmp_url': 'rtmp://a.rtmp.youtube.com/live2/',
            'stream_key': ''
        },
        'facebook': {
            'name': 'Facebook',
            'rtmp_url': 'rtmps://live-api-s.facebook.com:443/rtmp/',
            'stream_key': ''
        },
        'twitch': {
            'name': 'Twitch',
            'rtmp_url': 'rtmp://live.twitch.tv/app/',
            'stream_key': ''
        },
        'custom': {
            'name': 'Custom RTMP',
            'rtmp_url': '',
            'stream_key': ''
        }
    },
    'video_device': '/dev/video0',
    'audio_device': 'hw:2,0',
    'resolution': '1280x720',
    'framerate': '30',
    'bitrate': '2500k',
    'audio_bitrate': '128k',
    'audio_gain': 0.5  # 50% volume to reduce background noise
}

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_hostname():
    """Get the hostname"""
    return socket.gethostname()

def discovery_service():
    """UDP broadcast discovery service"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', DISCOVERY_PORT))
    
    print(f"Discovery service listening on port {DISCOVERY_PORT}")
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data == DISCOVERY_MESSAGE:
                # Respond with our information
                local_ip = get_local_ip()
                hostname = get_hostname()
                response = f"STREAM_CONTROL_RESPONSE|{hostname}|{local_ip}|5000"
                sock.sendto(response.encode(), addr)
                print(f"Discovery request from {addr}, responded with {local_ip}")
        except Exception as e:
            print(f"Discovery error: {e}")

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_stream_status():
    if PID_FILE.exists():
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is running
            os.kill(pid, 0)
            return {'running': True, 'pid': pid}
        except (OSError, ValueError):
            PID_FILE.unlink(missing_ok=True)
    return {'running': False}

def start_stream(platform, config):
    if get_stream_status()['running']:
        return {'success': False, 'error': 'Stream already running'}
    
    platform_config = config['platforms'].get(platform)
    if not platform_config or not platform_config.get('stream_key'):
        return {'success': False, 'error': 'Invalid platform or missing stream key'}
    
    rtmp_url = platform_config['rtmp_url'] + platform_config['stream_key']
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg',
        '-f', 'v4l2',
        '-input_format', 'mjpeg',
        '-video_size', config['resolution'],
        '-framerate', config['framerate'],
        '-i', config['video_device'],
        '-f', 'alsa',
        '-i', config['audio_device'],
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-maxrate', config['bitrate'],
        '-bufsize', str(int(config['bitrate'].rstrip('k')) * 2) + 'k',
        '-pix_fmt', 'yuv420p',
        '-g', '60',
        '-c:a', 'aac',
        '-b:a', config['audio_bitrate'],
        '-ar', '44100',
        '-f', 'flv',
        rtmp_url
    ]
    
    try:
        # Start ffmpeg process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp
        )
        
        # Save PID
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))
        
        return {'success': True, 'pid': process.pid}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def stop_stream():
    status = get_stream_status()
    if not status['running']:
        return {'success': False, 'error': 'No stream running'}
    
    try:
        pid = status['pid']
        # Send SIGTERM to process group
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)
        return {'success': True}
    except Exception as e:
        PID_FILE.unlink(missing_ok=True)
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    config = load_config()
    status = get_stream_status()
    return render_template('index.html', config=config, status=status)

@app.route('/preview')
def preview():
    return render_template('preview.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'GET':
        return jsonify(load_config())
    else:
        config = request.json
        save_config(config)
        return jsonify({'success': True})

@app.route('/api/status')
def api_status():
    return jsonify(get_stream_status())

@app.route('/api/info')
def api_info():
    """Get system information for discovery"""
    return jsonify({
        'hostname': get_hostname(),
        'ip': get_local_ip(),
        'port': 5000,
        'mdns': f"{get_hostname()}.local"
    })

@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.json
    platform = data.get('platform')
    config = load_config()
    result = start_stream(platform, config)
    return jsonify(result)

@app.route('/api/stop', methods=['POST'])
def api_stop():
    result = stop_stream()
    return jsonify(result)

@app.route('/static/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


# Import additional modules for camera and stream management
import sys
sys.path.insert(0, "/home/jeff/stream-control")
from stream_manager import StreamManager
from camera_discovery import CameraDiscovery

# Initialize managers
stream_manager = StreamManager(Path.home() / "stream-control" / "pids")
camera_discovery = CameraDiscovery()

@app.route("/api/cameras")
def api_cameras():
    """Get list of available cameras"""
    cameras = camera_discovery.discover_usb_cameras()
    # Filter to actual capture devices (exclude internal Pi devices)
    usable_cameras = [
        c for c in cameras 
        if "C920" in c.get("name", "") or 
           "webcam" in c.get("name", "").lower() or
           c.get("path") in ["/dev/video0", "/dev/video1"]
    ]
    return jsonify({"cameras": usable_cameras})

@app.route("/api/streams/incoming")
def api_streams_incoming():
    """Get list of incoming RTMP streams"""
    streams = stream_manager.get_incoming_streams()
    return jsonify({"streams": streams})

@app.route("/api/streams/active")
def api_streams_active():
    """Get list of active rebroadcast streams"""
    streams = stream_manager.get_active_streams()
    return jsonify({"streams": streams})

@app.route("/dashboard")
def dashboard():
    """Stream monitoring dashboard"""
    return render_template("dashboard.html")

@app.route("/api/sources")
def api_sources():
    """Get list of all available stream sources"""
    sources = []

    # Add USB cameras
    cameras = camera_discovery.discover_usb_cameras()
    for cam in cameras:
        # Only show actual capture devices (video0, video2, etc - not metadata devices like video1)
        # C920 creates video0 (capture) and video1 (metadata), we only want video0
        if ("C920" in cam.get("name", "") or "webcam" in cam.get("name", "").lower()) and cam.get("path") == "/dev/video0":
            # Get device name for HLS path
            device_name = cam["path"].split('/')[-1]  # e.g., "video0"
            sources.append({
                "id": cam["path"],
                "name": f"{cam['name']} (USB)",
                "type": "usb",
                "path": cam["path"],
                "hls_url": f"http://{get_local_ip()}:8888/preview_{device_name}/index.m3u8"
            })

    # Add incoming RTMP streams
    streams = stream_manager.get_incoming_streams()
    for stream in streams:
        sources.append({
            "id": f"rtmp://localhost:1935/{stream['name']}",
            "name": f"{stream['name']} (RTMP Stream)",
            "type": "rtmp",
            "url": f"rtmp://localhost:1935/{stream['name']}",
            "hls_url": f"http://{get_local_ip()}:8888/{stream['name']}/index.m3u8"
        })

    return jsonify({"sources": sources})

@app.route("/api/rebroadcast/start", methods=['POST'])
def api_rebroadcast_start():
    """Start rebroadcasting a source to a platform"""
    data = request.json
    source_id = data.get('source_id')
    platform = data.get('platform')

    if not source_id or not platform:
        return jsonify({"success": False, "error": "Missing source_id or platform"})

    # Get config
    config = load_config()

    # Handle special "preview" platform for local preview only
    if platform == 'preview':
        source_name = source_id.split('/')[-1]  # e.g., "video0"
        target_url = f"rtmp://localhost:1935/preview_{source_name}"
        stream_id = f"preview_{source_name}"
    else:
        # Get platform config
        if platform not in config['platforms']:
            return jsonify({"success": False, "error": "Invalid platform"})

        platform_config = config['platforms'][platform]

        # Build target RTMP URL
        target_url = f"{platform_config['rtmp_url']}{platform_config['stream_key']}"

        # Generate stream ID
        source_name = source_id.split('/')[-1]  # e.g., "video0" or "gopro1"
        stream_id = f"{source_name}_to_{platform}"

    # Start rebroadcast
    result = stream_manager.start_rebroadcast(
        stream_id=stream_id,
        source_url=source_id,
        target_url=target_url,
        config=config
    )

    if result['success']:
        return jsonify({"success": True, "stream_id": stream_id})
    else:
        return jsonify({"success": False, "error": result.get('error', 'Unknown error')})

@app.route("/api/rebroadcast/stop", methods=['POST'])
def api_rebroadcast_stop():
    """Stop a rebroadcast stream"""
    data = request.json
    stream_id = data.get('stream_id')

    if not stream_id:
        return jsonify({"success": False, "error": "Missing stream_id"})

    result = stream_manager.stop_rebroadcast(stream_id)
    return jsonify(result)

@app.route("/api/rebroadcast/status")
def api_rebroadcast_status():
    """Get status of all rebroadcast streams"""
    streams = stream_manager.get_active_streams()
    return jsonify({"streams": streams})

if __name__ == "__main__":
    # Ensure config exists
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
    
    # Start discovery service in background thread
    discovery_thread = threading.Thread(target=discovery_service, daemon=True)
    discovery_thread.start()
    
    # Print access information
    local_ip = get_local_ip()
    hostname = get_hostname()
    print("\\n" + "="*60)
    print("Stream Control Service Started")
    print("="*60)
    print(f"Access via IP:       http://{local_ip}:5000")
    print(f"Access via mDNS:     http://{hostname}.local:5000")
    print(f"Discovery Port:      {DISCOVERY_PORT}/UDP")
    print("="*60 + "\\n")
    
    # Run on all interfaces so it can be accessed from network
    app.run(host="0.0.0.0", port=5000, debug=False)
