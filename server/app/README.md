# Stream Control System - Multi-Camera Setup

## System Overview

Your Raspberry Pi is now set up as a multi-camera streaming hub with the following capabilities:

### Core Components

1. **MediaMTX RTMP Server** (Port 1935)
   - Receives RTMP streams from GoPro cameras and other sources
   - Also provides RTSP (8554), HLS (8888), WebRTC (8889)
   - Status: Running as systemd service

2. **Stream Control Web App** (Port 5000)
   - Web interface for managing streams
   - Camera discovery
   - Multi-stream rebroadcast control

3. **Camera Discovery**
   - USB cameras (like your Logitech C920)
   - Incoming RTMP streams
   - Network camera scanning

## How to Stream from GoPro

### GoPro Configuration

1. **On your GoPro:**
   - Go to Settings → Connections → Wired Connections → USB Connection
   - Enable "GoPro Connect" or "Live Streaming"
   - Some models: Settings → Connections → Live Streaming

2. **GoPro RTMP Output:**
   - Configure your GoPro to stream to:
   ```
   RTMP URL: rtmp://192.168.86.31:1935/gopro1
   Stream Key: (leave empty or use "live")
   ```
   - For multiple GoPros, use different stream names:
     - GoPro #1: `rtmp://192.168.86.31:1935/gopro1`
     - GoPro #2: `rtmp://192.168.86.31:1935/gopro2`
     - etc.

3. **Alternative: GoPro App:**
   - Some GoPro models can stream via the GoPro app
   - Set custom RTMP server to your Pi's IP

## System Architecture

```
[GoPro Camera] ----RTMP----> [MediaMTX Server] -----> [Stream Manager]
[USB Camera]   ----v4l2----> [on Raspberry Pi]        [Re-broadcasts to]
                                                        - YouTube
                                                        - Facebook
                                                        - Twitch
                                                        - Custom RTMP
```

## Services Running

### MediaMTX RTMP Server
```bash
# Status
sudo systemctl status mediamtx

# View incoming streams
curl http://localhost:9997/v3/paths/list | jq

# Logs
sudo journalctl -u mediamtx -f
```

**Ports:**
- 1935: RTMP input (for GoPro and cameras)
- 8554: RTSP output
- 8888: HLS output (web playback)
- 8889: WebRTC
- 9997: API

### Stream Control App
```bash
# Status
sudo systemctl status stream-control

# Logs
sudo journalctl -u stream-control -f

# Restart
sudo systemctl restart stream-control
```

**Access:**
- http://192.168.86.31:5000
- http://raspberrypi.local:5000

## Python Modules

### Camera Discovery
```python
from camera_discovery import CameraDiscovery

discovery = CameraDiscovery()

# Discover USB cameras
usb_cameras = discovery.discover_usb_cameras()

# Scan for IP cameras
ip_cameras = discovery.scan_ip_cameras()
```

### Stream Manager
```python
from stream_manager import StreamManager

manager = StreamManager('/home/jeff/stream-control/pids')

# Get active rebroadcast streams
active = manager.get_active_streams()

# Get incoming RTMP streams
incoming = manager.get_incoming_streams()

# Start rebroadcasting a stream
manager.start_rebroadcast(
    stream_id='gopro1_to_youtube',
    source_url='rtmp://localhost:1935/gopro1',
    target_url='rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY',
    config={
        'bitrate': '2500k',
        'audio_bitrate': '128k',
        'preset': 'veryfast'
    }
)

# Stop a stream
manager.stop_rebroadcast('gopro1_to_youtube')
```

## Manual Stream Re-broadcasting

If you want to manually re-broadcast from command line:

```bash
# Re-broadcast incoming RTMP to YouTube
ffmpeg -i rtmp://localhost:1935/gopro1 \
  -c:v libx264 -preset veryfast -b:v 2500k \
  -c:a aac -b:a 128k \
  -f flv rtmp://a.rtmp.youtube.com/live2/YOUR_KEY

# Re-broadcast USB camera
ffmpeg -f v4l2 -i /dev/video0 \
  -f alsa -i hw:2,0 \
  -c:v libx264 -preset veryfast -b:v 2500k \
  -c:a aac -b:a 128k \
  -f flv rtmp://a.rtmp.youtube.com/live2/YOUR_KEY
```

## Monitoring Incoming Streams

```bash
# List all active streams
curl http://localhost:9997/v3/paths/list

# Watch for incoming connections
sudo journalctl -u mediamtx -f | grep "publish"

# Test if stream is working
ffplay rtmp://localhost:1935/gopro1
# or
ffplay rtsp://localhost:8554/gopro1
```

## Network Discovery

From any computer on your network:
```bash
python3 ~/discover-stream.py
```

## Firewall Ports

Make sure these ports are accessible:
- 1935/TCP: RTMP input
- 5000/TCP: Web interface
- 8554/TCP: RTSP (optional)
- 8888/TCP: HLS (optional)
- 48888/UDP: Discovery service

## File Locations

- App: `/home/jeff/stream-control/`
- Config: `/home/jeff/stream-control/config.json`
- MediaMTX Config: `/etc/mediamtx.yml`
- Stream PIDs: `/home/jeff/stream-control/pids/`

## Troubleshooting

### GoPro not connecting?
1. Check GoPro is on same network
2. Verify RTMP URL format
3. Check MediaMTX logs: `sudo journalctl -u mediamtx -f`
4. Try RTSP instead: some GoPros prefer RTSP

### Stream quality issues?
- Lower bitrate in config
- Change preset to "faster" or "ultrafast"
- Check network bandwidth

### Multiple cameras stuttering?
- Raspberry Pi CPU may be limited
- Lower resolution/framerate
- Use hardware encoding if available
- Consider upgrading to Pi 5

## Next Steps

1. **Test GoPro Connection:**
   - Configure GoPro to stream to Pi
   - Monitor MediaMTX logs to see connection
   - View stream: `ffplay rtmp://localhost:1935/gopro1`

2. **Web UI Enhancement:**
   - The basic UI is working at port 5000
   - Full multi-stream UI can be added next
   - Currently supports single-stream mode

3. **Add More Cameras:**
   - Each GoPro gets unique stream name
   - USB cameras can be added
   - Mix and match sources

## Quick Start Commands

```bash
# Check everything is running
sudo systemctl status mediamtx stream-control

# Watch for incoming streams
curl http://localhost:9997/v3/paths/list

# Test camera discovery
python3 ~/stream-control/camera_discovery.py

# Test stream manager
python3 ~/stream-control/stream_manager.py

# Access web interface
open http://192.168.86.31:5000
```

