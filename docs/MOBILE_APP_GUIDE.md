# Mobile App Installation Guide

The Stream Control interface is a Progressive Web App (PWA) that works on all mobile devices.

## What is a PWA?

A Progressive Web App is a website that works like a native app:
- ✅ Installs to your home screen
- ✅ Works offline
- ✅ Full-screen experience (no browser UI)
- ✅ Fast and responsive
- ✅ Updates automatically

**No app store needed!**

---

## Installation on iPhone / iPad

### Step 1: Open in Safari
**Important:** Must use Safari, not Chrome

1. Open **Safari** browser
2. Navigate to: `http://raspberrypi.local:5000`
   - Or use IP address: `http://192.168.86.31:5000`

### Step 2: Add to Home Screen

1. Tap the **Share** button (square with arrow) at the bottom
2. Scroll down and tap **"Add to Home Screen"**
3. Name it **"Stream Control"** (or whatever you like)
4. Tap **"Add"**

### Step 3: Launch the App

1. Find the app icon on your home screen
2. Tap to open
3. App opens in full-screen mode!

---

## Installation on Android

### Step 1: Open in Chrome

1. Open **Chrome** browser
2. Navigate to: `http://raspberrypi.local:5000`

### Step 2: Install

Chrome will show an "Install" prompt at the bottom:
- Tap **"Install"** or **"Add to Home Screen"**

**OR manually add:**
1. Tap the **menu** (⋮) in top-right
2. Select **"Add to Home screen"**
3. Tap **"Add"**

### Step 3: Launch

- App icon appears on home screen
- Tap to open
- Works like a native app!

---

## Features

Once installed, you can:

### Control Panel
- Start/stop streams
- Select platforms (YouTube, Facebook, Twitch)
- Adjust quality settings
- View network info

### Dashboard (📊 View Dashboard button)
- Monitor incoming RTMP streams
- View connected cameras
- See active rebroadcasts
- Preview camera feeds (HLS)

---

## Finding Your Pi on Any Network

If you change networks or can't find the Pi:

### Option 1: Use mDNS
```
http://raspberrypi.local:5000
```
Works on most networks automatically!

### Option 2: Discovery Tool

From a computer on the same network:
```bash
cd FFmpegRemoteApp/server/app
python3 discover.py
```

Shows the Pi's IP address

### Option 3: Check Router

1. Log into your router's admin page
2. Look for "raspberrypi" in connected devices
3. Note the IP address
4. Visit `http://<that-ip>:5000`

---

## Offline Features

The app caches resources so it works offline:
- Interface loads even without connection
- Can view cached camera list
- Settings are saved locally

**Note:** You need network connection to actually stream, but the UI works offline.

---

## Updating the App

**No manual updates needed!**

The app automatically updates when:
- You visit the page
- The server is updated

To force an update:
1. Open the app
2. Pull down to refresh
3. New version loads automatically

---

## Removing the App

### iPhone
1. Long-press the app icon
2. Tap **"Remove App"**
3. Tap **"Delete App"**

### Android
1. Long-press the app icon
2. Drag to **"Uninstall"** or **"Remove"**

---

## Troubleshooting

### App won't install on iPhone
- ✅ Make sure you're using **Safari** (not Chrome)
- ✅ Check iOS is up to date
- ✅ Try restarting Safari

### Can't connect to Pi
- ✅ Make sure phone and Pi are on same network
- ✅ Try `http://raspberrypi.local:5000`
- ✅ Try IP address instead of hostname
- ✅ Run discovery tool to find Pi

### App not updating
- ✅ Pull down to refresh
- ✅ Close and reopen app
- ✅ Clear browser cache
- ✅ Reinstall the app

---

## Advanced: Use Over Internet

Want to control your Pi from anywhere?

### Option 1: VPN
1. Set up VPN server on your network
2. Connect phone to VPN
3. Access Pi as if on local network

### Option 2: Port Forwarding (Not Recommended)
1. Forward port 5000 on your router
2. Use your public IP
3. **Security Risk** - Not recommended without HTTPS

### Option 3: Tailscale/ZeroTier
1. Install Tailscale on Pi and phone
2. Creates secure virtual network
3. Access Pi from anywhere securely

---

## Why PWA Instead of Native App?

### Advantages
- ✅ Works on **all devices** (iPhone, Android, iPad, tablets)
- ✅ **No app store** approval needed
- ✅ **Instant updates** - just update the Pi
- ✅ **One codebase** - works everywhere
- ✅ **No installation size** - lives on your server
- ✅ **Always in sync** - everyone gets same version

### When You'd Want Native App
- ❌ Need to work completely offline (no Pi connection)
- ❌ Need push notifications from Pi
- ❌ Want to publish to app store
- ❌ Need access to special phone features

For controlling a local device on your network (like this), **PWA is ideal!**

---

## Next Steps

1. **Install the app** on your phone following steps above
2. **Test the dashboard** - Tap "📊 View Dashboard"
3. **Connect a GoPro** and see it appear in incoming streams
4. **Start streaming** to your favorite platform

Enjoy your mobile streaming control center! 🎥
