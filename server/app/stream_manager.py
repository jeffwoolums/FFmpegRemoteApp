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

class StreamManager:
    def __init__(self, pid_dir):
        self.pid_dir = Path(pid_dir)
        self.pid_dir.mkdir(exist_ok=True)
        self.mediamtx_api = "http://127.0.0.1:9997/v3"
    
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
                    if item.get('sourceReady'):
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
            cmd = [
                'ffmpeg',
                '-f', 'v4l2',
                '-input_format', 'mjpeg',
                '-video_size', config.get('resolution', '1280x720'),
                '-framerate', config.get('framerate', '30'),
                '-i', source_url,
                '-f', 'alsa',
                '-i', config.get('audio_device', 'hw:2,0'),
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
