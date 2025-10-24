#!/usr/bin/env python3
"""
GPS Data Reader for VK-162 USB GPS
Reads GPS data from gpsd and provides it for stream overlays
"""

import time
import json
import sys
from gps import gps, WATCH_ENABLE, WATCH_NEWSTYLE
from datetime import datetime
from pathlib import Path

class GPSReader:
    def __init__(self, output_file='/tmp/gps_data.json'):
        self.output_file = Path(output_file)
        self.session = None
        self.last_valid_data = {
            'latitude': 0.0,
            'longitude': 0.0,
            'altitude': 0.0,
            'speed_mph': 0.0,
            'speed_kph': 0.0,
            'heading': 0.0,
            'satellites': 0,
            'fix_quality': 0,
            'timestamp': '',
            'location_name': 'No GPS Lock',
            'has_fix': False
        }

    def connect(self):
        """Connect to gpsd"""
        try:
            self.session = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
            print("✅ Connected to gpsd")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to gpsd: {e}")
            print("   Make sure gpsd is running: sudo systemctl start gpsd")
            return False

    def meters_per_sec_to_mph(self, mps):
        """Convert meters per second to miles per hour"""
        return mps * 2.23694

    def meters_per_sec_to_kph(self, mps):
        """Convert meters per second to kilometers per hour"""
        return mps * 3.6

    def meters_to_feet(self, meters):
        """Convert meters to feet"""
        return meters * 3.28084

    def get_cardinal_direction(self, heading):
        """Convert heading degrees to cardinal direction (N, NE, E, etc.)"""
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = int((heading + 22.5) / 45.0) % 8
        return directions[index]

    def read_data(self):
        """Read GPS data from gpsd and return parsed data"""
        try:
            report = self.session.next()

            if report['class'] == 'TPV':  # Time-Position-Velocity report
                # Update data if we have a valid fix
                if hasattr(report, 'mode') and report.mode >= 2:  # 2D or 3D fix
                    self.last_valid_data['has_fix'] = True
                    self.last_valid_data['fix_quality'] = report.mode

                    if hasattr(report, 'lat'):
                        self.last_valid_data['latitude'] = round(report.lat, 6)

                    if hasattr(report, 'lon'):
                        self.last_valid_data['longitude'] = round(report.lon, 6)

                    if hasattr(report, 'alt'):
                        self.last_valid_data['altitude'] = round(self.meters_to_feet(report.alt), 1)

                    if hasattr(report, 'speed'):
                        self.last_valid_data['speed_mph'] = round(self.meters_per_sec_to_mph(report.speed), 1)
                        self.last_valid_data['speed_kph'] = round(self.meters_per_sec_to_kph(report.speed), 1)

                    if hasattr(report, 'track'):
                        self.last_valid_data['heading'] = round(report.track, 1)
                        self.last_valid_data['heading_cardinal'] = self.get_cardinal_direction(report.track)

                    if hasattr(report, 'time'):
                        self.last_valid_data['timestamp'] = report.time

                    # Simple location name (would use reverse geocoding API for real names)
                    lat = self.last_valid_data['latitude']
                    lon = self.last_valid_data['longitude']
                    self.last_valid_data['location_name'] = f"{lat:.4f}°, {lon:.4f}°"

                else:
                    self.last_valid_data['has_fix'] = False
                    self.last_valid_data['location_name'] = 'Acquiring GPS...'

            elif report['class'] == 'SKY':  # Satellite info
                if hasattr(report, 'satellites'):
                    self.last_valid_data['satellites'] = len(report.satellites)

            return self.last_valid_data

        except KeyError:
            pass
        except StopIteration:
            print("❌ Lost connection to gpsd")
            return None
        except Exception as e:
            print(f"⚠️  Error reading GPS: {e}")
            return None

        return self.last_valid_data

    def save_data(self, data):
        """Save GPS data to JSON file for FFmpeg overlay"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving GPS data: {e}")

    def run(self, update_interval=0.5):
        """Main loop - read GPS data and save to file"""
        print("🛰️  GPS Reader started")
        print(f"📁 Output file: {self.output_file}")
        print("⏱️  Update interval: {:.1f} seconds".format(update_interval))
        print("")

        if not self.connect():
            return

        try:
            while True:
                data = self.read_data()
                if data:
                    self.save_data(data)

                    # Print status every second
                    if time.time() % 1 < update_interval:
                        status = "🟢 FIX" if data['has_fix'] else "🔴 NO FIX"
                        speed = f"{data['speed_mph']:.1f} MPH"
                        sats = f"{data['satellites']} sats"
                        print(f"{status} | {speed} | {sats} | {data['location_name']}")

                time.sleep(update_interval)

        except KeyboardInterrupt:
            print("\n👋 GPS Reader stopped")
        except Exception as e:
            print(f"❌ Fatal error: {e}")

if __name__ == '__main__':
    reader = GPSReader()
    reader.run()
