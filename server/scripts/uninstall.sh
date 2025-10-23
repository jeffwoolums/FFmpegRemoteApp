#!/bin/bash
#
# FFmpeg Remote Stream Control - Uninstaller
#

set -e

echo "======================================"
echo "FFmpeg Remote Stream Control Uninstaller"
echo "======================================"
echo ""

read -p "This will remove all stream control components. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

INSTALL_DIR="$HOME/stream-control"

echo "Stopping services..."
sudo systemctl stop stream-control || true
sudo systemctl stop mediamtx || true

echo "Disabling services..."
sudo systemctl disable stream-control || true
sudo systemctl disable mediamtx || true

echo "Removing service files..."
sudo rm -f /etc/systemd/system/stream-control.service
sudo rm -f /etc/systemd/system/mediamtx.service
sudo rm -f /etc/avahi/services/stream-control.service

echo "Removing MediaMTX..."
sudo rm -f /usr/local/bin/mediamtx
sudo rm -f /etc/mediamtx.yml

echo "Removing application directory..."
rm -rf "$INSTALL_DIR"

sudo systemctl daemon-reload

echo ""
echo "Uninstallation complete!"
echo ""
echo "Note: The following packages were NOT removed:"
echo "  - ffmpeg, v4l-utils, alsa-utils, python3-pip"
echo "  - Python packages"
echo ""
echo "To remove them manually:"
echo "  sudo apt-get remove ffmpeg v4l-utils alsa-utils"
echo ""
