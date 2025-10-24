#!/bin/bash
# GPS Setup Script for VK-162 G-Mouse USB GPS
# Sets up gpsd to read GPS data from the VK-162 device

echo "========================================="
echo "VK-162 GPS Setup for Stream Overlays"
echo "========================================="
echo ""

# Install gpsd and client tools
echo "📦 Installing gpsd and dependencies..."
sudo apt-get update
sudo apt-get install -y gpsd gpsd-clients python3-gps

# Stop gpsd service
echo "🛑 Stopping gpsd service..."
sudo systemctl stop gpsd
sudo systemctl stop gpsd.socket

# Configure gpsd
echo "⚙️  Configuring gpsd..."
sudo tee /etc/default/gpsd > /dev/null << 'EOF'
# Default settings for the gpsd init script and the hotplug wrapper.

# Start the gpsd daemon automatically at boot time
START_DAEMON="true"

# Use USB hotplugging to add new USB devices automatically to the daemon
USBAUTO="true"

# Devices gpsd should collect to at boot time.
# They need to be read/writable, either by user gpsd or the group dialout.
DEVICES="/dev/ttyACM0 /dev/ttyUSB0"

# Other options you want to pass to gpsd
GPSD_OPTIONS="-n -G"
EOF

# Add user to dialout group for GPS access
echo "👤 Adding user 'jeff' to dialout group..."
sudo usermod -a -G dialout jeff

# Enable and start gpsd
echo "🚀 Enabling and starting gpsd service..."
sudo systemctl enable gpsd
sudo systemctl enable gpsd.socket
sudo systemctl start gpsd.socket
sudo systemctl start gpsd

echo ""
echo "✅ GPS setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Plug in your VK-162 GPS USB dongle"
echo "   2. Wait 30-60 seconds for GPS lock (needs clear view of sky)"
echo "   3. Test with: cgps -s"
echo "   4. Check device with: ls -la /dev/ttyACM* /dev/ttyUSB*"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Check GPS is detected: lsusb | grep -i prolific"
echo "   - Check gpsd status: sudo systemctl status gpsd"
echo "   - Restart gpsd: sudo systemctl restart gpsd"
echo "   - View GPS data: gpsmon"
echo ""
