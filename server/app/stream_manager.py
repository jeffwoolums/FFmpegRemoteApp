#!/usr/bin/env python3
"""
Multi-Stream Manager
Manages multiple simultaneous streams from various sources
"""

import os
import json
import subprocess
import signal
import requests
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class StreamManager:
    def __init__(self, pid_dir):
        self.pid_dir = Path(pid_dir)
        self.pid_dir.mkdir(exist_ok=True)
        self.mediamtx_api = "http://127.0.0.1:9997/v3"
        self.gps_data_file = Path('/tmp/gps_data.json')

    def get_gps_data(self) -> Dict:
        """Read current GPS data from file"""
        if self.gps_data_file.exists():
            try:
                with open(self.gps_data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'has_fix': False,
            'speed_mph': 0,
            'speed_kph': 0,
            'latitude': 0,
            'longitude': 0,
            'altitude': 0,
            'heading_cardinal': 'N',
            'location_name': 'No GPS'
        }

    def build_overlay_filter(self, config: Dict) -> Dict:
        """Build FFmpeg overlay filters (text and image) based on config and GPS data"""
        overlays = config.get('overlays', {})

        if not overlays.get('enabled', False):
            return {'text_filters': None, 'has_minimap': False, 'minimap_position': 'bottom-right'}

        template = overlays.get('template', 'minimal')
        font_size = overlays.get('font_size', 24)
        font_color = overlays.get('font_color', 'white')

        filters = []
        y_pos = 10  # Starting Y position

        # Custom title at top
        custom_title = overlays.get('custom_title', '')
        if custom_title:
            filters.append(
                f"drawtext=text='{custom_title}':x=10:y={y_pos}:"
                f"fontsize={font_size + 4}:fontcolor={font_color}:box=1:boxcolor=black@0.7:boxborderw=5"
            )
            y_pos += font_size + 15

        # Build overlay text based on template and enabled elements
        overlay_lines = []

        if template == 'minimal':
            if overlays.get('show_speed'):
                overlay_lines.append("Speed\\: %{eif\\:0\\:d} MPH")
            if overlays.get('show_location'):
                overlay_lines.append("Location\\: GPS Data")

        elif template == 'racing':
            if overlays.get('show_speed'):
                # Large speed display
                filters.append(
                    f"drawtext=text='SPEED':x=10:y={y_pos}:"
                    f"fontsize={font_size}:fontcolor=gray"
                )
                y_pos += font_size + 5
                filters.append(
                    f"drawtext=text='-- MPH':x=10:y={y_pos}:"
                    f"fontsize={font_size * 2}:fontcolor=red:box=1:boxcolor=black@0.8:boxborderw=8"
                )
                y_pos += (font_size * 2) + 15
            if overlays.get('show_heading'):
                overlay_lines.append("Heading\\: N")

        elif template == 'adventure':
            if overlays.get('show_location'):
                overlay_lines.append("Location\\: Acquiring...")
            if overlays.get('show_elevation'):
                overlay_lines.append("Elevation\\: -- ft")
            if overlays.get('show_speed'):
                overlay_lines.append("Speed\\: -- MPH")
            if overlays.get('show_heading'):
                overlay_lines.append("Heading\\: --")

        elif template == 'professional':
            # Full telemetry layout
            if overlays.get('show_speed'):
                overlay_lines.append("SPD\\: -- MPH")
            if overlays.get('show_elevation'):
                overlay_lines.append("ALT\\: -- ft")
            if overlays.get('show_heading'):
                overlay_lines.append("HDG\\: --")
            if overlays.get('show_location'):
                overlay_lines.append("GPS\\: --.---- N, --.---- W")
            if overlays.get('show_time'):
                overlay_lines.append("TIME\\: --\\:--\\:--")

        # Add each line as a separate drawtext filter
        for line in overlay_lines:
            filters.append(
                f"drawtext=text='{line}':x=10:y={y_pos}:"
                f"fontsize={font_size}:fontcolor={font_color}:box=1:boxcolor=black@0.7:boxborderw=5"
            )
            y_pos += font_size + 10

        # Add time display if enabled (bottom right)
        if overlays.get('show_time') and template != 'professional':
            filters.append(
                f"drawtext=text='%{{localtime}}':x=w-tw-10:y=h-th-10:"
                f"fontsize={font_size - 4}:fontcolor={font_color}:box=1:boxcolor=black@0.7:boxborderw=5"
            )

        text_filter = ','.join(filters) if filters else None

        # Check if mini-map is enabled
        has_minimap = overlays.get('minimap_enabled', False)
        minimap_position = overlays.get('minimap_position', 'bottom-right')

        return {
            'text_filters': text_filter,
            'has_minimap': has_minimap,
            'minimap_position': minimap_position,
            'minimap_size': overlays.get('minimap_size', 400)
        }

    def get_active_streams(self) -> List[Dict]:
        """Get list of active rebroadcast streams"""
        streams = []
        for pid_file in self.pid_dir.glob("stream_*.pid"):
            try:
                with open(pid_file, 'r') as f:
                    data = json.load(f)
                    pid = data.get('pid')
                    
                    # Check if process is still running
                    if pid:
                        try:
                            os.kill(pid, 0)
                            streams.append(data)
                        except OSError:
                            # Process not running, remove pid file
                            pid_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"Error reading {pid_file}: {e}")
        
        return streams
    
    def get_incoming_streams(self) -> List[Dict]:
        """Get incoming RTMP streams from MediaMTX"""
        try:
            response = requests.get(f"{self.mediamtx_api}/paths/list", timeout=2)
            if response.status_code == 200:
                data = response.json()
                incoming = []
                
                # MediaMTX returns list of active paths
                for item in data.get('items', []):
                    path_name = item.get('name', '')
                    # Check if it has active readers or publishers
                    if item.get('ready'):
                        incoming.append({
                            'name': path_name,
                            'url': f'rtmp://localhost:1935/{path_name}',
                            'rtsp_url': f'rtsp://localhost:8554/{path_name}',
                            'hls_url': f'http://localhost:8888/{path_name}',
                            'readers': item.get('readers', 0),
                            'publishers': item.get('bytesReceived', 0) > 0
                        })
                
                return incoming
        except Exception as e:
            print(f"Error getting incoming streams: {e}")
        
        return []
    
    def start_rebroadcast(self, stream_id: str, source_url: str, target_url: str, 
                         config: Dict) -> Dict:
        """Start rebroadcasting a stream"""
        pid_file = self.pid_dir / f"stream_{stream_id}.pid"
        
        # Check if already running
        if pid_file.exists():
            return {'success': False, 'error': 'Stream already running'}
        
        # Build ffmpeg command based on source type
        if source_url.startswith('rtmp://') or source_url.startswith('rtsp://'):
            # Network stream input
            cmd = [
                'ffmpeg',
                '-i', source_url,
                '-c:v', 'libx264',
                '-preset', config.get('preset', 'veryfast'),
                '-b:v', config.get('bitrate', '2500k'),
                '-maxrate', config.get('bitrate', '2500k'),
                '-bufsize', str(int(config.get('bitrate', '2500k').rstrip('k')) * 2) + 'k',
                '-pix_fmt', 'yuv420p',
                '-g', '60',
                '-c:a', 'aac',
                '-b:a', config.get('audio_bitrate', '128k'),
                '-ar', '44100',
                '-f', 'flv',
                target_url
            ]
        else:
            # USB camera input
            # Get audio gain setting (default to 0.5 = 50% volume to reduce background noise)
            audio_gain = config.get('audio_gain', 0.5)

            cmd = [
                'ffmpeg',
                '-f', 'v4l2',
                '-input_format', 'mjpeg',
                '-video_size', config.get('resolution', '1280x720'),
                '-framerate', config.get('framerate', '30'),
                '-i', source_url,
                '-f', 'alsa',
                '-i', config.get('audio_device', 'hw:2,0'),
            ]

            # Build overlay filters
            overlay_data = self.build_overlay_filter(config)
            text_filters = overlay_data['text_filters']
            has_minimap = overlay_data['has_minimap']
            minimap_position = overlay_data['minimap_position']

            # Add mini-map as additional input if enabled
            minimap_file = Path('/tmp/minimap_overlay.png')
            if has_minimap and minimap_file.exists():
                cmd.extend(['-loop', '1', '-i', str(minimap_file)])

            # Build filter complex for overlays
            if has_minimap and text_filters:
                # Both mini-map and text overlays
                # Calculate minimap position
                if minimap_position == 'bottom-right':
                    overlay_pos = 'x=W-w-10:y=H-h-10'
                elif minimap_position == 'bottom-left':
                    overlay_pos = 'x=10:y=H-h-10'
                elif minimap_position == 'top-right':
                    overlay_pos = 'x=W-w-10:y=10'
                elif minimap_position == 'top-left':
                    overlay_pos = 'x=10:y=10'
                else:
                    overlay_pos = 'x=W-w-10:y=H-h-10'

                filter_complex = f"[0:v][2:v]overlay={overlay_pos}[vtmp];[vtmp]{text_filters}[v]"
                cmd.extend(['-filter_complex', filter_complex, '-map', '[v]', '-map', '1:a'])

            elif has_minimap:
                # Only mini-map overlay
                if minimap_position == 'bottom-right':
                    overlay_pos = 'x=W-w-10:y=H-h-10'
                elif minimap_position == 'bottom-left':
                    overlay_pos = 'x=10:y=H-h-10'
                elif minimap_position == 'top-right':
                    overlay_pos = 'x=W-w-10:y=10'
                elif minimap_position == 'top-left':
                    overlay_pos = 'x=10:y=10'
                else:
                    overlay_pos = 'x=W-w-10:y=H-h-10'

                filter_complex = f"[0:v][2:v]overlay={overlay_pos}"
                cmd.extend(['-filter_complex', filter_complex, '-map', '1:a'])

            elif text_filters:
                # Only text overlays
                cmd.extend(['-vf', text_filters])

            cmd.extend([
                '-c:v', 'libx264',
                '-preset', config.get('preset', 'veryfast'),
                '-b:v', config.get('bitrate', '2500k'),
                '-maxrate', config.get('bitrate', '2500k'),
                '-bufsize', str(int(config.get('bitrate', '2500k').rstrip('k')) * 2) + 'k',
                '-pix_fmt', 'yuv420p',
                '-g', '60',
                '-af', f'volume={audio_gain}',  # Audio filter for volume control
                '-c:a', 'aac',
                '-b:a', config.get('audio_bitrate', '128k'),
                '-ar', '44100',
                '-f', 'flv',
                target_url
            ])
        
        try:
            # Start ffmpeg process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp
            )
            
            # Save stream information
            stream_info = {
                'id': stream_id,
                'pid': process.pid,
                'source': source_url,
                'target': target_url,
                'config': config
            }
            
            with open(pid_file, 'w') as f:
                json.dump(stream_info, f)
            
            return {'success': True, 'pid': process.pid, 'stream_id': stream_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_rebroadcast(self, stream_id: str) -> Dict:
        """Stop a rebroadcast stream"""
        pid_file = self.pid_dir / f"stream_{stream_id}.pid"
        
        if not pid_file.exists():
            return {'success': False, 'error': 'Stream not found'}
        
        try:
            with open(pid_file, 'r') as f:
                data = json.load(f)
                pid = data.get('pid')
            
            if pid:
                try:
                    # Send SIGTERM to process group
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except:
                    pass
            
            pid_file.unlink(missing_ok=True)
            return {'success': True}
        except Exception as e:
            pid_file.unlink(missing_ok=True)
            return {'success': False, 'error': str(e)}
    
    def stop_all_rebroadcasts(self):
        """Stop all active rebroadcast streams"""
        streams = self.get_active_streams()
        for stream in streams:
            self.stop_rebroadcast(stream['id'])

if __name__ == '__main__':
    # Test the stream manager
    manager = StreamManager('/tmp/stream-control-pids')
    
    print("Active rebroadcast streams:")
    for stream in manager.get_active_streams():
        print(f"  - {stream['id']}: {stream['source']} -> {stream['target']}")
    
    print("\nIncoming streams to MediaMTX:")
    for stream in manager.get_incoming_streams():
        print(f"  - {stream['name']}: {stream['url']}")
