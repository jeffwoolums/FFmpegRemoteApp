#!/usr/bin/env python3
"""
Live Mini-Map Updater Service
Continuously updates mini-map with current GPS position for stream overlay
"""

import json
import time
import sys
from pathlib import Path
from minimap_generator import MiniMapGenerator

class LiveMiniMapUpdater:
    def __init__(self, tracks_dir='tracks', update_interval=1.0):
        self.tracks_dir = Path(tracks_dir)
        self.gps_data_file = Path('/tmp/gps_data.json')
        self.update_interval = update_interval
        self.generator = MiniMapGenerator(tracks_dir)
        self.current_track = None
        self.overlay_output = Path('/tmp/minimap_overlay.png')

        print("🗺️  Live Mini-Map Updater Service")
        print(f"📁 Tracks directory: {self.tracks_dir}")
        print(f"📍 GPS data file: {self.gps_data_file}")
        print(f"🖼️  Output overlay: {self.overlay_output}")
        print(f"⏱️  Update interval: {self.update_interval}s")

    def load_gps_data(self) -> dict:
        """Load current GPS data from file"""
        if not self.gps_data_file.exists():
            return None

        try:
            with open(self.gps_data_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading GPS data: {e}")
            return None

    def load_config(self) -> dict:
        """Load overlay configuration"""
        config_file = Path.home() / 'stream-control' / 'config.json'

        if not config_file.exists():
            return {'overlays': {'minimap_enabled': False, 'minimap_track': 'baja1000_2025'}}

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('overlays', {})
        except:
            return {'minimap_enabled': False, 'minimap_track': 'baja1000_2025'}

    def update_minimap(self):
        """Update mini-map with current GPS position"""
        # Load GPS data
        gps_data = self.load_gps_data()

        if not gps_data or not gps_data.get('has_fix'):
            print("🔴 No GPS fix - using static map")
            # Generate static map
            if self.current_track:
                try:
                    static_map = self.generator.generate_static_minimap(
                        self.current_track, size=(400, 400)
                    )
                    # Copy to overlay location
                    import shutil
                    shutil.copy(static_map, self.overlay_output)
                except Exception as e:
                    print(f"⚠️  Error generating static map: {e}")
            return

        # Get current position
        lat = gps_data.get('latitude', 0)
        lon = gps_data.get('longitude', 0)
        speed = gps_data.get('speed_mph', 0)

        if lat == 0 and lon == 0:
            return

        # Generate mini-map with current position
        try:
            output_path = self.generator.generate_minimap_with_position(
                self.current_track, lat, lon, size=(400, 400)
            )

            # Copy to standard overlay location
            import shutil
            shutil.copy(output_path, self.overlay_output)

            print(f"✅ Mini-map updated: {lat:.4f}, {lon:.4f} @ {speed:.1f} MPH", end='\r')

        except Exception as e:
            print(f"⚠️  Error updating mini-map: {e}")

    def run(self):
        """Main loop - continuously update mini-map"""
        print("\n🚀 Starting mini-map updater service...\n")

        # Load configuration
        overlay_config = self.load_config()
        self.current_track = overlay_config.get('minimap_track', 'baja1000_2025')

        print(f"🏁 Tracking: {self.current_track}")
        print(f"{'='*60}\n")

        # Generate initial static map
        try:
            static_map = self.generator.generate_static_minimap(
                self.current_track, size=(400, 400)
            )
            import shutil
            shutil.copy(static_map, self.overlay_output)
            print("✅ Initial mini-map generated\n")
        except Exception as e:
            print(f"❌ Error generating initial map: {e}\n")
            return

        # Main update loop
        try:
            while True:
                self.update_minimap()
                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            print("\n\n👋 Mini-map updater stopped")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")

if __name__ == '__main__':
    # Get tracks directory from command line or use default
    tracks_dir = sys.argv[1] if len(sys.argv) > 1 else '/home/jeff/stream-control/tracks'

    # Update interval in seconds
    update_interval = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

    updater = LiveMiniMapUpdater(tracks_dir, update_interval)
    updater.run()
