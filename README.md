# FFmpeg Remote Stream Control

A complete multi-camera live streaming solution for Raspberry Pi with remote web control. Stream from GoPro cameras, USB webcams, and IP cameras to YouTube, Facebook, Twitch, and custom RTMP destinations.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

## Features

- 🎥 **Multi-Camera Support**: GoPro (RTMP), USB webcams, IP cameras
- 📡 **RTMP Server**: Receive streams from multiple cameras simultaneously
- 🔄 **Multi-Stream Rebroadcast**: Send different cameras to different platforms at once
- 🌐 **Web Interface**: Control everything from your phone or computer
- 📱 **PWA Support**: Install as an app on iPhone/Android
- 🔍 **Auto-Discovery**: Find your Pi on any network automatically
- ⚙️ **Camera Discovery**: Automatically detect USB and IP cameras
- 🚀 **Easy Installation**: One-command setup script

## Quick Start

### Requirements

- Raspberry Pi 4 or 5 (recommended)
- Raspberry Pi OS (Debian 12+ / Bookworm)
- Network connection
- USB webcam or GoPro camera (optional)

### Installation on Raspberry Pi

```bash
# Clone the repository
git clone https://github.com/jeffwoolums/FFmpegRemoteApp.git
cd FFmpegRemoteApp/server

# Run the installer
chmod +x scripts/install.sh
./scripts/install.sh
```

The installer will:
- Install ffmpeg and dependencies
- Set up MediaMTX RTMP server
- Install the web control interface
- Configure auto-start services
- Set up network discovery

### Accessing the Interface

After installation, access the web interface:

**Direct IP:**
```
http://<raspberry-pi-ip>:5000
```

**mDNS (Bonjour):**
```
http://raspberrypi.local:5000
```

**Auto-Discovery:**
```bash
# From any computer on the same network
cd FFmpegRemoteApp/server/app
python3 discover.py
```

## Streaming from GoPro

### Configure Your GoPro

1. **On GoPro Camera:**
   - Go to Settings → Connections → Live Streaming
   - Or: Settings → Connections → Wired Connections → USB Connection

2. **Set RTMP URL:**
   ```
   RTMP URL: rtmp://<raspberry-pi-ip>:1935/gopro1
   Stream Key: live (or leave empty)
   ```

3. **Multiple GoPros:**
   - GoPro #1: `rtmp://<pi-ip>:1935/gopro1`
   - GoPro #2: `rtmp://<pi-ip>:1935/gopro2`
   - GoPro #3: `rtmp://<pi-ip>:1935/gopro3`

4. **Start Streaming** on the GoPro

### Monitor Incoming Streams

```bash
# SSH into your Pi
ssh pi@raspberrypi.local

# List active streams
curl http://localhost:9997/v3/paths/list

# Watch logs
sudo journalctl -u mediamtx -f
```

## Using USB Cameras

USB cameras (like the Logitech C920) are automatically detected. Access them through the web interface or programmatically:

```python
from camera_discovery import CameraDiscovery

discovery = CameraDiscovery()
cameras = discovery.discover_usb_cameras()

for camera in cameras:
    print(f"{camera['name']} at {camera['path']}")
```

## Rebroadcasting Streams

### Via Web Interface

1. Open the web interface
2. Select platform (YouTube/Facebook/Twitch)
3. Enter your stream key
4. Choose camera source
5. Click "Start Stream"

### Via Python API

```python
from stream_manager import StreamManager

manager = StreamManager('/home/pi/stream-control/pids')

# Rebroadcast GoPro to YouTube
manager.start_rebroadcast(
    stream_id='gopro1_youtube',
    source_url='rtmp://localhost:1935/gopro1',
    target_url='rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY',
    config={
        'bitrate': '2500k',
        'audio_bitrate': '128k',
        'preset': 'veryfast'
    }
)

# Stop the stream
manager.stop_rebroadcast('gopro1_youtube')
```

### Via Command Line

```bash
# Rebroadcast incoming RTMP to YouTube
ffmpeg -i rtmp://localhost:1935/gopro1 \
  -c:v libx264 -preset veryfast -b:v 2500k \
  -c:a aac -b:a 128k \
  -f flv rtmp://a.rtmp.youtube.com/live2/YOUR_KEY
```

## Architecture

```
┌─────────────┐
│   GoPro 1   │──RTMP──┐
├─────────────┤        │
│   GoPro 2   │──RTMP──┤
├─────────────┤        │     ┌──────────────┐      ┌─────────────┐
│ USB Webcam  │──v4l2──┼────►│  MediaMTX    │─────►│   Stream    │──┬──► YouTube
├─────────────┤        │     │ RTMP Server  │      │   Manager   │  │
│  IP Camera  │──RTSP──┤     │ Port 1935    │      │  (ffmpeg)   │  ├──► Facebook
└─────────────┘        │     └──────────────┘      └─────────────┘  │
                       │                                              └──► Twitch
                       │     ┌──────────────┐
                       └────►│ Web Control  │◄──────── [Phone/Browser]
                             │  Port 5000   │
                             └──────────────┘
```

## Project Structure

```
FFmpegRemoteApp/
├── server/                  # Raspberry Pi server component
│   ├── app/                 # Main application
│   │   ├── app.py          # Flask web server
│   │   ├── stream_manager.py    # Stream management
│   │   ├── camera_discovery.py  # Camera detection
│   │   ├── templates/      # HTML templates
│   │   └── static/         # CSS, JS, icons
│   ├── scripts/            # Installation scripts
│   │   ├── install.sh     # Installer
│   │   └── uninstall.sh   # Uninstaller
│   └── requirements.txt    # Python dependencies
├── client/                  # Standalone web client (future)
└── docs/                   # Documentation
```

## System Components

### MediaMTX RTMP Server
- **Purpose**: Receives RTMP streams from cameras
- **Port**: 1935 (RTMP), 8554 (RTSP), 8888 (HLS)
- **Config**: `/etc/mediamtx.yml`
- **Service**: `sudo systemctl status mediamtx`

### Stream Control Web App
- **Purpose**: Web interface for managing streams
- **Port**: 5000 (HTTP)
- **Location**: `~/stream-control/`
- **Service**: `sudo systemctl status stream-control`

### Discovery Service
- **Purpose**: UDP broadcast for network discovery
- **Port**: 48888 (UDP)
- **mDNS**: Avahi service on port 5353

## Configuration

### Stream Settings

Edit `~/stream-control/config.json`:

```json
{
  "platforms": {
    "youtube": {
      "rtmp_url": "rtmp://a.rtmp.youtube.com/live2/",
      "stream_key": ""
    },
    "facebook": {
      "rtmp_url": "rtmps://live-api-s.facebook.com:443/rtmp/",
      "stream_key": ""
    }
  },
  "video_device": "/dev/video0",
  "resolution": "1280x720",
  "framerate": "30",
  "bitrate": "2500k",
  "audio_bitrate": "128k"
}
```

### MediaMTX Server

Edit `/etc/mediamtx.yml` for advanced RTMP server configuration.

## Mobile App Installation (PWA)

### iPhone/iPad
1. Open Safari
2. Navigate to `http://raspberrypi.local:5000`
3. Tap the Share button
4. Select "Add to Home Screen"
5. Tap "Add"

### Android
1. Open Chrome
2. Navigate to the URL
3. Tap the menu (⋮)
4. Select "Add to Home screen"

The app will work offline and function like a native app!

## Troubleshooting

### GoPro Not Connecting

```bash
# Check if MediaMTX is running
sudo systemctl status mediamtx

# View MediaMTX logs
sudo journalctl -u mediamtx -f

# Verify GoPro can reach the Pi
ping <raspberry-pi-ip>

# Check firewall
sudo ufw status
```

### Stream Quality Issues

- **Lower bitrate**: Change to 1500k or 1000k
- **Change preset**: Use "ultrafast" instead of "veryfast"
- **Reduce resolution**: Use 720p instead of 1080p
- **Check CPU usage**: `htop`

### Can't Find Pi on Network

```bash
# From another computer
python3 discover.py

# Or use mDNS
ping raspberrypi.local

# Check Avahi
sudo systemctl status avahi-daemon
```

### Service Not Starting

```bash
# Check service logs
sudo journalctl -u stream-control -n 50

# Restart services
sudo systemctl restart mediamtx
sudo systemctl restart stream-control

# Check for port conflicts
sudo netstat -tulpn | grep -E '(1935|5000|8554)'
```

## Management Commands

```bash
# Service status
sudo systemctl status mediamtx stream-control

# Start/stop services
sudo systemctl start stream-control
sudo systemctl stop stream-control

# View logs
sudo journalctl -u stream-control -f
sudo journalctl -u mediamtx -f

# List active streams
curl http://localhost:9997/v3/paths/list | jq

# Discover cameras
python3 ~/stream-control/camera_discovery.py

# Test network discovery
python3 ~/stream-control/discover.py
```

## Ports Used

| Port  | Protocol | Purpose                  |
|-------|----------|--------------------------|
| 1935  | TCP      | RTMP input (cameras)     |
| 5000  | TCP      | Web interface            |
| 8554  | TCP      | RTSP output              |
| 8888  | TCP      | HLS streaming            |
| 8889  | TCP      | WebRTC                   |
| 9997  | TCP      | MediaMTX API             |
| 48888 | UDP      | Discovery service        |
| 5353  | UDP      | mDNS (Avahi)            |

## Performance Tips

### Raspberry Pi 4
- Max 2-3 simultaneous 1080p streams
- Use "veryfast" or "faster" preset
- Consider 720p for more streams

### Raspberry Pi 5
- Can handle 4-6 simultaneous 1080p streams
- Can use "fast" preset
- Better hardware encoding support

### Optimization
```bash
# Check CPU temperature
vcgencmd measure_temp

# Monitor CPU usage
htop

# Check encoding performance
sudo journalctl -u stream-control -f | grep fps
```

## Development

### Running in Development Mode

```bash
cd ~/stream-control
python3 app.py
```

### API Endpoints

- `GET /api/status` - Stream status
- `POST /api/start` - Start stream
- `POST /api/stop` - Stop stream
- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration
- `GET /api/info` - System information

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Author

Jeff Woolums (https://github.com/jeffwoolums)

## Acknowledgments

- [MediaMTX](https://github.com/bluenviron/mediamtx) - RTMP/RTSP server
- [FFmpeg](https://ffmpeg.org/) - Video processing
- [Flask](https://flask.palletsprojects.com/) - Web framework

## Support

- Issues: https://github.com/jeffwoolums/FFmpegRemoteApp/issues
- Discussions: https://github.com/jeffwoolums/FFmpegRemoteApp/discussions

## Roadmap

- [ ] Multi-camera composition (PiP, side-by-side)
- [ ] Recording to local storage
- [ ] Stream scheduling
- [ ] Chat integration (YouTube, Twitch)
- [ ] Stream analytics
- [ ] Mobile app (React Native)
- [ ] Cloud deployment option
- [ ] Docker containers
