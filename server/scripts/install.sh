#!/bin/bash
#
# FFmpeg Remote Stream Control - Raspberry Pi Installation Script
#
# This script installs and configures the stream control server on a Raspberry Pi
#

set -e

echo "======================================"
echo "FFmpeg Remote Stream Control Installer"
echo "======================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "WARNING: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "Please run as normal user (not root/sudo)"
   exit 1
fi

INSTALL_DIR="$HOME/stream-control"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$(dirname "$SCRIPT_DIR")/app"

echo "Installation directory: $INSTALL_DIR"
echo ""

# Update system
echo "[1/7] Updating system packages..."
sudo apt-get update -qq

# Install dependencies
echo "[2/7] Installing dependencies..."
sudo apt-get install -y \
    ffmpeg \
    v4l-utils \
    alsa-utils \
    python3-pip \
    python3-venv \
    avahi-daemon \
    wget \
    curl

# Create installation directory
echo "[3/7] Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/pids"
mkdir -p "$INSTALL_DIR/logs"

# Copy application files
echo "[4/7] Copying application files..."
cp -r "$APP_DIR"/* "$INSTALL_DIR/"

# Install Python dependencies
echo "[5/7] Installing Python packages..."
cd "$INSTALL_DIR"
pip3 install --user -r ../requirements.txt

# Install MediaMTX
echo "[6/7] Installing MediaMTX RTMP server..."
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    MTX_ARCH="arm64v8"
elif [ "$ARCH" = "armv7l" ]; then
    MTX_ARCH="armv7"
else
    MTX_ARCH="arm64v8"
fi

cd /tmp
wget -q "https://github.com/bluenviron/mediamtx/releases/download/v1.9.3/mediamtx_v1.9.3_linux_${MTX_ARCH}.tar.gz"
tar -xzf "mediamtx_v1.9.3_linux_${MTX_ARCH}.tar.gz"
sudo mv mediamtx /usr/local/bin/
sudo mv mediamtx.yml /etc/
rm "mediamtx_v1.9.3_linux_${MTX_ARCH}.tar.gz"

# Configure MediaMTX
echo "[7/7] Configuring services..."
sudo tee /etc/mediamtx.yml > /dev/null <<EOF
api: yes
apiAddress: 127.0.0.1:9997
rtmp: yes
rtmpAddress: :1935
rtsp: yes
rtspAddress: :8554
hls: yes
hlsAddress: :8888
paths:
  all:
EOF

# Create systemd service for MediaMTX
sudo tee /etc/systemd/system/mediamtx.service > /dev/null <<EOF
[Unit]
Description=MediaMTX RTMP/RTSP Server
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/mediamtx /etc/mediamtx.yml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Stream Control
sudo tee /etc/systemd/system/stream-control.service > /dev/null <<EOF
[Unit]
Description=Stream Control Web Interface
After=network.target mediamtx.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Avahi service advertisement
sudo tee /etc/avahi/services/stream-control.service > /dev/null <<EOF
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">Stream Control on %h</name>
  <service>
    <type>_http._tcp</type>
    <port>5000</port>
    <txt-record>path=/</txt-record>
    <txt-record>service=stream-control</txt-record>
  </service>
</service-group>
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable mediamtx
sudo systemctl enable stream-control
sudo systemctl start mediamtx
sleep 2
sudo systemctl start stream-control

echo ""
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""
echo "Services Status:"
sudo systemctl status mediamtx --no-pager -l | head -3
sudo systemctl status stream-control --no-pager -l | head -3
echo ""
echo "Access the web interface at:"
echo "  http://$(hostname -I | awk '{print $1}'):5000"
echo "  http://$(hostname).local:5000"
echo ""
echo "RTMP Server (for cameras):"
echo "  rtmp://$(hostname -I | awk '{print $1}'):1935/<stream-name>"
echo ""
echo "Next steps:"
echo "  1. Configure your GoPro or camera to stream to the RTMP server"
echo "  2. Access the web interface from any device on your network"
echo "  3. Use the discovery tool on other devices: python3 discover.py"
echo ""
echo "View logs:"
echo "  sudo journalctl -u stream-control -f"
echo "  sudo journalctl -u mediamtx -f"
echo ""
