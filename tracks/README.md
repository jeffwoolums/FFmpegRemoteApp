# Race Track Files

This folder contains race track data files for GPS overlay and mini-map visualization.

## Directory Structure

```
tracks/
├── kml/          - KML track files (Google Earth format)
├── gpx/          - GPX track files (GPS Exchange format)
├── images/       - Track map images (PNG/JPG)
├── processed/    - Auto-generated track data (DO NOT EDIT)
└── README.md     - This file
```

## How to Add a New Track

1. **Add your track file:**
   - Place KML files in `kml/` folder
   - Place GPX files in `gpx/` folder
   - (Optional) Place track map images in `images/` folder

2. **File naming convention:**
   - Use descriptive names: `laguna_seca.kml`, `sonoma_raceway.gpx`
   - No spaces (use underscores): `road_atlanta.kml` ✅, `road atlanta.kml` ❌

3. **Track data will be auto-processed:**
   - The system will automatically convert tracks to overlay format
   - Processed data goes in `processed/` folder
   - Do not manually edit files in `processed/`

## Supported Formats

### KML Files
- Google Earth track files
- Can include waypoints, start/finish lines, sectors
- Exported from Google Earth, RaceRender, or similar

### GPX Files
- Standard GPS track format
- Contains latitude/longitude coordinates
- Exported from Garmin, Strava, or GPS devices

### Track Images (Optional)
- PNG or JPG format
- Overhead view of track
- Will be used as mini-map background
- Recommended size: 400x400 to 800x800 pixels

## Example File Contents

### KML Example
Your KML should contain track boundaries and optionally:
- Start/finish line
- Sector markers
- Pit lane
- Elevation data

### GPX Example
Your GPX should contain a track with coordinates forming the racing line or track boundaries.

## Track Metadata

For best results, create a `tracks.json` file with track information:

```json
{
  "laguna_seca": {
    "name": "WeatherTech Raceway Laguna Seca",
    "location": "Monterey, CA",
    "length_miles": 2.238,
    "turns": 11,
    "kml_file": "kml/laguna_seca.kml",
    "gpx_file": "gpx/laguna_seca.gpx",
    "image_file": "images/laguna_seca.png"
  },
  "sonoma": {
    "name": "Sonoma Raceway",
    "location": "Sonoma, CA",
    "length_miles": 2.52,
    "turns": 12,
    "kml_file": "kml/sonoma_raceway.kml"
  }
}
```

## How Tracks Are Used

1. **Mini-Map Overlay**: Track outline shown in corner of stream with live GPS position
2. **Sector Detection**: Automatically detect which sector of track you're in
3. **Lap Timing**: Detect when you cross start/finish line
4. **Location Names**: Show current corner/sector name

## Tips

- **Higher Resolution is Better**: More GPS points = smoother track outline
- **Include Elevation**: If your track file has elevation data, it will be used
- **Multiple Laps**: GPX files with multiple laps will be averaged for best racing line
- **Start/Finish**: Mark start/finish line in your KML for lap detection

## Processing Your Tracks

Once you add track files, run:
```bash
python3 process_tracks.py
```

This will:
- Parse all KML/GPX files
- Generate track outline images
- Create position lookup tables
- Build sector detection data
- Output to `processed/` folder

## Need Help?

- **Creating KML**: Use Google Earth to trace track
- **Exporting GPX**: Record a lap with GPS device or app
- **Track Images**: Screenshot from Google Maps satellite view
