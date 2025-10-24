#!/usr/bin/env python3
"""
Race Track Processor
Parses KML/GPX files and generates track data for mini-map overlays
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple
import math

class TrackProcessor:
    def __init__(self, tracks_dir='tracks'):
        self.tracks_dir = Path(tracks_dir)
        self.kml_dir = self.tracks_dir / 'kml'
        self.gpx_dir = self.tracks_dir / 'gpx'
        self.images_dir = self.tracks_dir / 'images'
        self.processed_dir = self.tracks_dir / 'processed'
        self.processed_dir.mkdir(exist_ok=True)

    def parse_kml(self, kml_file: Path) -> List[Tuple[float, float, float]]:
        """Parse KML file and extract coordinates (lat, lon, alt)"""
        print(f"📄 Parsing KML: {kml_file.name}")

        tree = ET.parse(kml_file)
        root = tree.getroot()

        # KML uses namespaces
        namespaces = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'gx': 'http://www.google.com/kml/ext/2.2'
        }

        coordinates = []

        # Find all coordinate elements
        for elem in root.iter():
            if 'coordinates' in elem.tag:
                coord_text = elem.text.strip()
                # KML coordinates are: longitude,latitude,altitude
                for line in coord_text.split('\n'):
                    line = line.strip()
                    if line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            alt = float(parts[2]) if len(parts) > 2 else 0.0
                            coordinates.append((lat, lon, alt))

        print(f"  ✅ Found {len(coordinates)} coordinate points")
        return coordinates

    def parse_gpx(self, gpx_file: Path) -> List[Tuple[float, float, float]]:
        """Parse GPX file and extract track points (lat, lon, alt)"""
        print(f"📄 Parsing GPX: {gpx_file.name}")

        tree = ET.parse(gpx_file)
        root = tree.getroot()

        # GPX uses namespace
        namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}

        coordinates = []

        # Find all track points
        for trkpt in root.findall('.//gpx:trkpt', namespace):
            lat = float(trkpt.get('lat'))
            lon = float(trkpt.get('lon'))

            # Try to find elevation
            ele_elem = trkpt.find('gpx:ele', namespace)
            alt = float(ele_elem.text) if ele_elem is not None else 0.0

            coordinates.append((lat, lon, alt))

        # Also check for route points
        for rtept in root.findall('.//gpx:rtept', namespace):
            lat = float(rtept.get('lat'))
            lon = float(rtept.get('lon'))

            ele_elem = rtept.find('gpx:ele', namespace)
            alt = float(ele_elem.text) if ele_elem is not None else 0.0

            coordinates.append((lat, lon, alt))

        print(f"  ✅ Found {len(coordinates)} track points")
        return coordinates

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates in meters (Haversine formula)"""
        R = 6371000  # Earth radius in meters

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def simplify_track(self, coordinates: List[Tuple[float, float, float]],
                      tolerance_meters: float = 100.0) -> List[Tuple[float, float, float]]:
        """Simplify track by removing points closer than tolerance"""
        if len(coordinates) < 2:
            return coordinates

        print(f"🔄 Simplifying track (tolerance: {tolerance_meters}m)...")

        simplified = [coordinates[0]]

        for coord in coordinates[1:]:
            last = simplified[-1]
            distance = self.calculate_distance(last[0], last[1], coord[0], coord[1])

            if distance >= tolerance_meters:
                simplified.append(coord)

        print(f"  ✅ Reduced from {len(coordinates)} to {len(simplified)} points ({len(simplified)/len(coordinates)*100:.1f}%)")
        return simplified

    def calculate_bounds(self, coordinates: List[Tuple[float, float, float]]) -> Dict:
        """Calculate bounding box for track"""
        lats = [c[0] for c in coordinates]
        lons = [c[1] for c in coordinates]
        alts = [c[2] for c in coordinates]

        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons),
            'min_alt': min(alts),
            'max_alt': max(alts),
            'center_lat': (min(lats) + max(lats)) / 2,
            'center_lon': (min(lons) + max(lons)) / 2
        }

    def calculate_total_distance(self, coordinates: List[Tuple[float, float, float]]) -> float:
        """Calculate total track distance in miles"""
        total_meters = 0.0

        for i in range(len(coordinates) - 1):
            dist = self.calculate_distance(
                coordinates[i][0], coordinates[i][1],
                coordinates[i+1][0], coordinates[i+1][1]
            )
            total_meters += dist

        return total_meters / 1609.34  # Convert to miles

    def process_track(self, track_id: str, track_info: Dict) -> Dict:
        """Process a track and generate all necessary data"""
        print(f"\n{'='*60}")
        print(f"🏁 Processing Track: {track_info['name']}")
        print(f"{'='*60}")

        # Load track data
        coordinates = []

        # Try GPX first (usually more detailed)
        gpx_file = self.tracks_dir / track_info.get('gpx_file', '')
        if gpx_file.exists():
            coordinates = self.parse_gpx(gpx_file)

        # If no GPX or failed, try KML
        if not coordinates:
            kml_file = self.tracks_dir / track_info.get('kml_file', '')
            if kml_file.exists():
                coordinates = self.parse_kml(kml_file)

        if not coordinates:
            print(f"❌ No valid track data found for {track_id}")
            return None

        # Simplify track for faster processing
        simplified_coords = self.simplify_track(coordinates, tolerance_meters=500)

        # Calculate track statistics
        bounds = self.calculate_bounds(simplified_coords)
        total_distance = self.calculate_total_distance(simplified_coords)

        print(f"\n📊 Track Statistics:")
        print(f"  Total Points: {len(coordinates):,} (simplified: {len(simplified_coords):,})")
        print(f"  Total Distance: {total_distance:.1f} miles")
        print(f"  Latitude Range: {bounds['min_lat']:.4f} to {bounds['max_lat']:.4f}")
        print(f"  Longitude Range: {bounds['min_lon']:.4f} to {bounds['max_lon']:.4f}")
        print(f"  Elevation Range: {bounds['min_alt']:.0f} to {bounds['max_alt']:.0f} meters")

        # Build processed data
        processed_data = {
            'track_id': track_id,
            'name': track_info['name'],
            'location': track_info.get('location', ''),
            'full_coordinates': simplified_coords,  # List of [lat, lon, alt]
            'bounds': bounds,
            'total_distance_miles': round(total_distance, 2),
            'total_points': len(simplified_coords),
            'map_image': track_info.get('image_file', ''),
            'generated_at': str(Path(__file__).stat().st_mtime)
        }

        # Save processed data
        output_file = self.processed_dir / f"{track_id}.json"
        with open(output_file, 'w') as f:
            json.dump(processed_data, f, indent=2)

        print(f"\n✅ Track data saved to: {output_file}")
        return processed_data

    def process_all_tracks(self):
        """Process all tracks from tracks.json"""
        tracks_json = self.tracks_dir / 'tracks.json'

        if not tracks_json.exists():
            print("❌ tracks.json not found")
            return

        with open(tracks_json, 'r') as f:
            tracks = json.load(f)

        print(f"\n🎯 Found {len(tracks)} track(s) to process\n")

        results = {}
        for track_id, track_info in tracks.items():
            result = self.process_track(track_id, track_info)
            if result:
                results[track_id] = result

        print(f"\n{'='*60}")
        print(f"✅ Processing Complete!")
        print(f"{'='*60}")
        print(f"Processed {len(results)} track(s)")
        print(f"Output directory: {self.processed_dir}")

        return results

if __name__ == '__main__':
    import sys

    # Get tracks directory from command line or use default
    tracks_dir = sys.argv[1] if len(sys.argv) > 1 else '../tracks'

    processor = TrackProcessor(tracks_dir)
    processor.process_all_tracks()
