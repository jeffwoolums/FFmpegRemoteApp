# Complete Setup Guide

This guide will walk you through setting up your FFmpeg Remote Stream Control system from scratch.

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Raspberry Pi Setup](#raspberry-pi-setup)
3. [Software Installation](#software-installation)
4. [Camera Configuration](#camera-configuration)
5. [First Stream](#first-stream)
6. [Mobile App Setup](#mobile-app-setup)
7. [Advanced Configuration](#advanced-configuration)

## Hardware Requirements

### Minimum Requirements
- **Raspberry Pi 4 Model B** (4GB RAM minimum)
- **MicroSD Card** (32GB+ recommended, Class 10)
- **Power Supply** (Official 5V 3A USB-C)
- **Network Connection** (Ethernet recommended, WiFi supported)

### Recommended Setup
- **Raspberry Pi 5** (8GB RAM)
- **Active Cooling** (Fan or heatsink case)
- **Ethernet Connection** (for stable streaming)
- **SSD Boot Drive** (optional, for better performance)

### Camera Options
- **GoPro** (Hero 7+, with live streaming feature)
- **USB Webcam** (Logitech C920, C922, or similar)
- **IP Camera** (with RTSP support)

## Raspberry Pi Setup

### 1. Flash Raspberry Pi OS

Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/)

1. **Choose OS**: Raspberry Pi OS (64-bit) - Debian Bookworm
2. **Choose Storage**: Your microSD card
3. **Settings** (gear icon):
   - Set hostname: `raspberrypi`
   - Enable SSH (password authentication)
   - Set username: `pi` (or your preference)
   - Set password: (choose a secure password)
   - Configure WiFi: (if not using Ethernet)
4. **Write** to card

### 2. First Boot

1. Insert microSD card into Raspberry Pi
2. Connect Ethernet cable
3. Connect power supply
4. Wait 2-3 minutes for first boot

### 3. Find Your Pi

**From Mac/Linux:**
```bash
# Try mDNS
ping raspberrypi.local

# Or scan network
nmap -sn 192.168.1.0/24 | grep -i raspberry
```

**From Windows:**
```powershell
ping raspberrypi.local
```

### 4. SSH Into Your Pi

```bash
ssh pi@raspberrypi.local
# Enter password when prompted
```

### 5. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

Wait for reboot, then reconnect via SSH.

## Software Installation

### Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/jeffwoolums/FFmpegRemoteApp.git
cd FFmpegRemoteApp/server

# Make installer executable
chmod +x scripts/install.sh

# Run installer
./scripts/install.sh
```

The installer will:
- Install ffmpeg and dependencies
- Set up MediaMTX RTMP server
- Install Flask web application
- Configure systemd services
- Set up network discovery

**Installation takes about 5-10 minutes.**

### Manual Installation

If you prefer manual installation, see [MANUAL_INSTALL.md](MANUAL_INSTALL.md)

### Verify Installation

```bash
# Check services are running
sudo systemctl status mediamtx
sudo systemctl status stream-control

# Check ports are listening
sudo netstat -tulpn | grep -E '(1935|5000)'

# Get your IP address
hostname -I
```

You should see:
- MediaMTX: ✓ active (running)
- stream-control: ✓ active (running)
- Port 1935: listening (RTMP)
- Port 5000: listening (HTTP)

## Camera Configuration

### USB Webcam

1. **Connect USB Camera** to Raspberry Pi
2. **Verify Detection:**
   ```bash
   v4l2-ctl --list-devices
   ```
3. **Test Camera:**
   ```bash
   ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 test.jpg
   ```

### GoPro Camera

#### GoPro Hero 9/10/11/12

1. **On GoPro**:
   - Swipe down → Preferences
   - Connections → Wired Connections
   - USB Connection → Live Streaming

2. **Set RTMP Server**:
   - URL: `rtmp://<your-pi-ip>:1935/gopro1`
   - Stream Key: `live` (or leave empty)

3. **Connect GoPro** to same WiFi network as Pi
4. **Start Streaming** on GoPro

#### GoPro Hero 7/8

1. **On GoPro**:
   - Swipe down → Preferences
   - Connections → Live Streaming
   - Set Up New Platform

2. **Configure**:
   - RTMP URL: `rtmp://<your-pi-ip>:1935/gopro1`
   - Stream Key: `live`

3. **Start Stream** from main screen

#### Using GoPro App

Some GoPros can stream via the mobile app:

1. **Connect GoPro** to app
2. **Go to Live Streaming**
3. **Choose Custom RTMP**
4. **Enter URL**: `rtmp://<pi-ip>:1935/gopro1`

### Verify Camera Stream

```bash
# On Raspberry Pi, check active streams
curl http://localhost:9997/v3/paths/list

# Watch logs
sudo journalctl -u mediamtx -f

# Test playback (requires display)
ffplay rtmp://localhost:1935/gopro1
```

## First Stream

### Get Your Stream Keys

#### YouTube
1. Go to [YouTube Studio](https://studio.youtube.com)
2. Click "Go Live"
3. Under "Stream settings", copy your **Stream key**

#### Facebook
1. Go to [Facebook Live Producer](https://www.facebook.com/live/producer)
2. Click "Use Stream Key"
3. Copy your **Stream key**

#### Twitch
1. Go to [Twitch Dashboard](https://dashboard.twitch.tv/settings/stream)
2. Under "Stream Key", click "Copy"

### Start Streaming

#### Via Web Interface

1. **Open Browser** on phone or computer
2. **Navigate to**:
   ```
   http://raspberrypi.local:5000
   ```
   Or use IP address:
   ```
   http://<your-pi-ip>:5000
   ```

3. **Select Platform**: YouTube / Facebook / Twitch
4. **Enter Stream Key**: Paste your key
5. **Adjust Settings** (optional):
   - Resolution: 720p or 1080p
   - Bitrate: 2500k (adjust based on internet speed)
6. **Click "Start Stream"**

#### Via Command Line

```bash
# Rebroadcast GoPro to YouTube
ffmpeg -i rtmp://localhost:1935/gopro1 \
  -c:v libx264 -preset veryfast \
  -b:v 2500k -maxrate 2500k -bufsize 5000k \
  -c:a aac -b:a 128k \
  -f flv rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY
```

### Monitor Your Stream

```bash
# Check stream status
curl http://localhost:9997/v3/paths/list | jq

# View logs
sudo journalctl -u stream-control -f

# Check CPU usage
htop

# Check temperature
vcgencmd measure_temp
```

## Mobile App Setup

### iPhone / iPad

1. **Open Safari** (must be Safari, not Chrome)
2. **Navigate to**: `http://raspberrypi.local:5000`
3. **Tap Share Button** (square with arrow)
4. **Scroll down**, tap "Add to Home Screen"
5. **Name it**: "Stream Control"
6. **Tap "Add"**

App icon appears on home screen!

### Android

1. **Open Chrome**
2. **Navigate to**: `http://raspberrypi.local:5000`
3. **Tap menu** (⋮)
4. **Select** "Add to Home screen"
5. **Tap "Add"**

### Features

- Works offline
- Full-screen mode
- Push notifications (future)
- Native feel

## Advanced Configuration

### Multiple Cameras

Stream multiple cameras to different platforms:

```python
from stream_manager import StreamManager

manager = StreamManager('/home/pi/stream-control/pids')

# GoPro 1 to YouTube
manager.start_rebroadcast(
    'gopro1_youtube',
    'rtmp://localhost:1935/gopro1',
    'rtmp://a.rtmp.youtube.com/live2/KEY1',
    {'bitrate': '2500k'}
)

# GoPro 2 to Facebook
manager.start_rebroadcast(
    'gopro2_facebook',
    'rtmp://localhost:1935/gopro2',
    'rtmps://live-api-s.facebook.com:443/rtmp/KEY2',
    {'bitrate': '2500k'}
)

# USB camera to Twitch
manager.start_rebroadcast(
    'usb_twitch',
    '/dev/video0',
    'rtmp://live.twitch.tv/app/KEY3',
    {'bitrate': '2500k', 'resolution': '1280x720'}
)
```

### Network Discovery

From any computer on your network:

```bash
cd FFmpegRemoteApp/server/app
python3 discover.py
```

Output:
```
✓ Found: raspberrypi
  IP Address:   192.168.1.100
  Web URL:      http://192.168.1.100:5000
  mDNS URL:     http://raspberrypi.local:5000
```

### Custom Bitrate Settings

Edit `~/stream-control/config.json`:

```json
{
  "resolution": "1280x720",
  "framerate": "30",
  "bitrate": "2500k",
  "audio_bitrate": "128k"
}
```

Recommended bitrates:
- **1080p60**: 6000k
- **1080p30**: 4500k
- **720p60**: 4500k
- **720p30**: 2500k
- **480p30**: 1500k

### Firewall Configuration

If using UFW firewall:

```bash
# Allow RTMP
sudo ufw allow 1935/tcp

# Allow web interface
sudo ufw allow 5000/tcp

# Allow discovery
sudo ufw allow 48888/udp
```

### Auto-Start on Boot

Services are already configured to start on boot. To verify:

```bash
sudo systemctl is-enabled mediamtx
sudo systemctl is-enabled stream-control
```

Both should show: `enabled`

### Backup Configuration

```bash
# Backup your configuration
cp ~/stream-control/config.json ~/config-backup.json

# Backup to another computer
scp pi@raspberrypi.local:~/stream-control/config.json ~/Desktop/
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting steps.

### Quick Fixes

**GoPro not connecting?**
```bash
# Check MediaMTX logs
sudo journalctl -u mediamtx -f

# Verify GoPro is on same network
ping <gopro-ip>

# Restart MediaMTX
sudo systemctl restart mediamtx
```

**Web interface not loading?**
```bash
# Check service
sudo systemctl status stream-control

# Check logs
sudo journalctl -u stream-control -n 50

# Restart service
sudo systemctl restart stream-control
```

**Poor stream quality?**
- Lower bitrate to 1500k
- Change resolution to 720p
- Use "ultrafast" preset
- Check internet upload speed: `speedtest-cli`

## Next Steps

1. **Test with one camera** first
2. **Add more cameras** once stable
3. **Experiment with settings** to find optimal quality
4. **Set up regular backups** of config
5. **Monitor system performance** during long streams

## Getting Help

- **Issues**: https://github.com/jeffwoolums/FFmpegRemoteApp/issues
- **Discussions**: https://github.com/jeffwoolums/FFmpegRemoteApp/discussions
- **Wiki**: https://github.com/jeffwoolums/FFmpegRemoteApp/wiki

Happy streaming! 🎥
