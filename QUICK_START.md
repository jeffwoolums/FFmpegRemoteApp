# Quick Start Guide

Get your FFmpeg Remote Stream Control system up and running in 10 minutes!

## Prerequisites

- Raspberry Pi 4/5 with Raspberry Pi OS
- Network connection
- GoPro or USB camera (optional for initial setup)

## Installation (5 minutes)

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local

# Clone and install
git clone https://github.com/jeffwoolums/FFmpegRemoteApp.git
cd FFmpegRemoteApp/server
chmod +x scripts/install.sh
./scripts/install.sh
```

Wait for installation to complete...

## Access the Interface (1 minute)

Open a web browser on any device:

```
http://raspberrypi.local:5000
```

Or find your Pi automatically:
```bash
cd FFmpegRemoteApp/server/app
python3 discover.py
```

## Connect a GoPro (2 minutes)

1. **On your GoPro:**
   - Settings → Connections → Live Streaming
   - RTMP URL: `rtmp://<your-pi-ip>:1935/gopro1`
   - Stream Key: `live` (or leave empty)

2. **Start streaming** on the GoPro

3. **Verify on Pi:**
   ```bash
   curl http://localhost:9997/v3/paths/list
   ```

## Start Streaming to YouTube (2 minutes)

1. **Get YouTube stream key:**
   - Go to https://studio.youtube.com
   - Click "Go Live"
   - Copy your stream key

2. **In the web interface:**
   - Select "YouTube"
   - Paste your stream key
   - Click "Start Stream"

3. **Watch your stream** go live on YouTube!

## That's It!

You're now streaming! 🎉

### Next Steps

- Add more cameras: Use different stream names (gopro2, gopro3, etc.)
- Install on iPhone: Open in Safari → Share → Add to Home Screen
- Stream to multiple platforms simultaneously
- Adjust quality settings in the web interface

### Getting Help

- Full documentation: See [README.md](README.md)
- Setup guide: See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)
- Issues: https://github.com/jeffwoolums/FFmpegRemoteApp/issues

### Quick Commands

```bash
# Check status
sudo systemctl status mediamtx stream-control

# View logs
sudo journalctl -u mediamtx -f

# List active streams
curl http://localhost:9997/v3/paths/list

# Restart services
sudo systemctl restart mediamtx stream-control
```

Happy streaming! 🎥
