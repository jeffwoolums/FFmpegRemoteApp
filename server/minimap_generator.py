#!/usr/bin/env python3
"""
Mini-Map Generator for Racing Overlays
Generates track mini-map with live GPS position marker
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

class MiniMapGenerator:
    def __init__(self, tracks_dir='tracks'):
        self.tracks_dir = Path(tracks_dir)
        self.processed_dir = self.tracks_dir / 'processed'
        self.images_dir = self.tracks_dir / 'images'
        self.overlay_dir = self.tracks_dir / 'processed' / 'overlays'
        self.overlay_dir.mkdir(exist_ok=True)

    def load_track_data(self, track_id: str) -> dict:
        """Load processed track data"""
        track_file = self.processed_dir / f"{track_id}.json"

        if not track_file.exists():
            raise FileNotFoundError(f"Track data not found: {track_file}")

        with open(track_file, 'r') as f:
            return json.load(f)

    def lat_lon_to_pixel(self, lat: float, lon: float, bounds: dict,
                        image_width: int, image_height: int) -> tuple:
        """Convert GPS coordinates to pixel coordinates on map image"""
        # Normalize coordinates to 0-1 range
        lat_norm = (lat - bounds['min_lat']) / (bounds['max_lat'] - bounds['min_lat'])
        lon_norm = (lon - bounds['min_lon']) / (bounds['max_lon'] - bounds['min_lon'])

        # Convert to pixel coordinates (flip Y axis for image coordinates)
        x = int(lon_norm * image_width)
        y = int((1 - lat_norm) * image_height)  # Flip Y

        return (x, y)

    def find_closest_point_on_track(self, current_lat: float, current_lon: float,
                                     track_coords: list) -> tuple:
        """Find the closest point on the track to current GPS position"""
        min_distance = float('inf')
        closest_point = None
        closest_index = 0

        for i, (lat, lon, alt) in enumerate(track_coords):
            # Simple distance calculation (good enough for short distances)
            dist = math.sqrt((lat - current_lat)**2 + (lon - current_lon)**2)

            if dist < min_distance:
                min_distance = dist
                closest_point = (lat, lon, alt)
                closest_index = i

        # Calculate progress percentage
        progress = (closest_index / len(track_coords)) * 100

        return closest_point, progress, closest_index

    def generate_base_minimap(self, track_id: str, size: tuple = (400, 400)) -> Image:
        """Generate base mini-map with track outline"""
        print(f"🗺️  Generating mini-map for {track_id}...")

        # Load track data
        track_data = self.load_track_data(track_id)

        # Load base map image
        map_image_path = self.tracks_dir / track_data['map_image']

        if not map_image_path.exists():
            # Create blank image if no map image available
            print(f"  ⚠️  Map image not found, creating blank background")
            img = Image.new('RGB', size, color='#1a1a1a')
        else:
            img = Image.open(map_image_path)
            # Resize to target size
            img = img.resize(size, Image.Resampling.LANCZOS)

        # Draw track path
        draw = ImageDraw.Draw(img)
        bounds = track_data['bounds']
        coords = track_data['full_coordinates']

        # Convert all track points to pixel coordinates
        pixels = []
        for lat, lon, alt in coords:
            x, y = self.lat_lon_to_pixel(lat, lon, bounds, size[0], size[1])
            pixels.append((x, y))

        # Draw track as line
        if len(pixels) > 1:
            draw.line(pixels, fill='#00ff00', width=3)  # Green track line

        print(f"  ✅ Base mini-map created ({size[0]}x{size[1]})")
        return img

    def add_position_marker(self, img: Image, lat: float, lon: float,
                           bounds: dict, color: str = '#ff0000') -> Image:
        """Add GPS position marker to mini-map"""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # Convert GPS to pixel
        x, y = self.lat_lon_to_pixel(lat, lon, bounds, width, height)

        # Draw position marker (circle with outer ring)
        marker_size = 12
        draw.ellipse(
            [x - marker_size, y - marker_size, x + marker_size, y + marker_size],
            fill=color,
            outline='white',
            width=2
        )

        # Draw center dot
        center_size = 4
        draw.ellipse(
            [x - center_size, y - center_size, x + center_size, y + center_size],
            fill='white'
        )

        return img

    def generate_minimap_with_position(self, track_id: str, current_lat: float,
                                      current_lon: float, size: tuple = (400, 400)) -> str:
        """Generate mini-map with current GPS position marked"""

        # Load track data
        track_data = self.load_track_data(track_id)

        # Generate base mini-map
        img = self.generate_base_minimap(track_id, size)

        # Add position marker
        img = self.add_position_marker(img, current_lat, current_lon, track_data['bounds'])

        # Find closest point on track for progress calculation
        closest, progress, index = self.find_closest_point_on_track(
            current_lat, current_lon, track_data['full_coordinates']
        )

        # Save to overlay directory
        output_path = self.overlay_dir / f"minimap_{track_id}_current.png"
        img.save(output_path, 'PNG')

        print(f"  ✅ Mini-map with position saved: {output_path}")
        print(f"  📊 Progress: {progress:.1f}% ({index}/{len(track_data['full_coordinates'])} points)")

        return str(output_path)

    def generate_static_minimap(self, track_id: str, size: tuple = (400, 400)) -> str:
        """Generate static mini-map without position marker (for testing)"""
        img = self.generate_base_minimap(track_id, size)

        # Save to overlay directory
        output_path = self.overlay_dir / f"minimap_{track_id}_static.png"
        img.save(output_path, 'PNG')

        print(f"  ✅ Static mini-map saved: {output_path}")
        return str(output_path)

if __name__ == '__main__':
    import sys

    # Example usage
    tracks_dir = sys.argv[1] if len(sys.argv) > 1 else '../tracks'

    generator = MiniMapGenerator(tracks_dir)

    # Generate static mini-map
    print("\n" + "="*60)
    print("🏁 Generating Baja 1000 Mini-Map")
    print("="*60 + "\n")

    static_map = generator.generate_static_minimap('baja1000_2025', size=(500, 500))

    # Example: Generate with a test position (Ensenada start area)
    print("\n" + "="*60)
    print("📍 Generating Mini-Map with Test Position")
    print("="*60 + "\n")

    test_lat = 31.801  # Near Ensenada start
    test_lon = -116.253
    position_map = generator.generate_minimap_with_position(
        'baja1000_2025', test_lat, test_lon, size=(500, 500)
    )

    print("\n" + "="*60)
    print("✅ Mini-Map Generation Complete!")
    print("="*60)
    print(f"Static map: {static_map}")
    print(f"Position map: {position_map}")
    print("\nUse these images in FFmpeg overlay filters!")
