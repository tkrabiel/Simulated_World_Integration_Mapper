import os
import requests
import geopandas as gpd
from pathlib import Path

MDAPI_BASE = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi"

def fetch_stations(station_type="waterlevels"):
    """Queries the NOAA server for a raw dump of available stations."""
    url = f"{MDAPI_BASE}/stations.json?type={station_type}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "stations" in data: return data["stations"]
    elif isinstance(data, list): return data
    return []

def filter_by_bounding_box(stations, min_lat, max_lat, min_lon, max_lon):
    """Filters raw station objects down to the M_COVR bounding coordinates."""
    result = []
    for s in stations:
        try:
            lat = float(s.get("lat", 0))
            lon = float(s.get("lng", s.get("lon", 0)))
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                result.append(s)
        except (ValueError, TypeError): continue
    return result

def fetch_harmonics(station_id):
    """Queries tidal harmonic constituents from NOAA."""
    url = f"{MDAPI_BASE}/stations/{station_id}/harcon.json"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_datums(station_id):
    """Queries physical benchmark elevations (like Mean Sea Level)."""
    url = f"{MDAPI_BASE}/stations/{station_id}/datums.json"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()

def feet_to_meters(value):
    return round(value * 0.3048, 5)

def build_environment_assets(output_dir, primary_station_str, tide_stations, current_stations):
    """Processes the chosen records and writes files out to disk."""
    if not output_dir:
        raise ValueError("Output directory must be configured.")
        
    os.makedirs(output_dir, exist_ok=True)
    station_id = primary_station_str.split(" - ")[0]
    
    print(f"\n[*] Fetching Harmonics for Primary Station: {station_id}...")
    harm_data = fetch_harmonics(station_id)
    consts = harm_data.get("HarmonicConstituents", harm_data.get("harmonicConstituents", []))
    
    harmonics_parsed = []
    for c in consts:
        amp_ft = float(c.get("amplitude", 0))
        harmonics_parsed.append({
            "name": c.get("name", ""),
            "amp_m": feet_to_meters(amp_ft),
            "speed": float(c.get("speed", 0)),
            "phase_gmt": float(c.get("phase_GMT", c.get("phase", 0)))
        })

    print("[*] Fetching MSL Datum...")
    constant_amp = 0.0
    try:
        datums = fetch_datums(station_id).get("datums", [])
        for d in datums:
            if d.get("name", "").upper() == "MSL":
                val = float(d.get("value", 0))
                if d.get("units", "feet").lower() == "feet": val = feet_to_meters(val)
                constant_amp = val
                break
    except Exception:
        print("    -> MSL not found. Defaulting constant amplitude to 0.0m.")

    # Write tide.ini
    print("[*] Generating tide.ini...")
    tide_content = f"Harmonics={len(harmonics_parsed)}\n\nAmplitude(0)={constant_amp:.5f}\n\n"
    for idx, c in enumerate(harmonics_parsed, 1):
        tide_content += f"Amplitude({idx})={c['amp_m']:.5f}\n"
        tide_content += f"Offset({idx})={c['phase_gmt']:.2f}\n"
        tide_content += f"Speed({idx})={c['speed']:.6f}\n\n"
        
    with open(os.path.join(output_dir, "tide.ini"), "w") as f:
        f.write(tide_content)

    # Write tidalstream.ini
    print(f"[*] Generating tidalstream.ini for {len(current_stations)} locations...")
    stream_content = f"Number={len(current_stations)}\nMeanRangeSprings=5.0\nMeanRangeNeaps=2.0\n\n"
    
    for i, s in enumerate(current_stations, 1):
        lat = float(s.get("lat", 0))
        lon = float(s.get("lng", s.get("lon", 0)))
        stream_content += f"Long({i})={lon:.5f}\nLat({i})={lat:.5f}\n\n"
        
        # Block 1: Neap Speeds
        for h in range(-6, 7):
            stream_content += f"SpeedN({i},{h})=0.5\n"
        stream_content += "\n"
        
        # Block 2: Spring Speeds
        for h in range(-6, 7):
            stream_content += f"SpeedS({i},{h})=1.0\n"
        stream_content += "\n"
        
        # Block 3: Directions
        for h in range(-6, 7):
            stream_content += f"Direction({i},{h})={0 if h < 0 else 180}\n"
        stream_content += "\n"
            
    if current_stations:
        with open(os.path.join(output_dir, "tidalstream.ini"), "w") as f:
            f.write(stream_content)

    # Write Summary File
    print("[*] Generating NOAA_Summary.txt...")
    summary = "=== SWIM Bridge Command Environmental Summary ===\n\n"
    summary += f"PRIMARY TIDE STATION (tide.ini):\n"
    summary += f"ID: {station_id}\nName: {primary_station_str.split(' - ')[1]}\n"
    summary += f"Harmonics Captured: {len(harmonics_parsed)}\n"
    summary += f"Constant Amplitude (MSL): {constant_amp:.5f} meters\n\n"
    
    summary += f"CURRENT PREDICTION STATIONS (tidalstream.ini):\n"
    if not current_stations: summary += "None found in bounding box.\n"
    for i, s in enumerate(current_stations, 1):
        name = s.get('name', 'Unknown')
        lat = float(s.get("lat", 0))
        lon = float(s.get("lng", s.get("lon", 0)))
        summary += f"{i}. {name} (Lat: {lat:.5f}, Lon: {lon:.5f})\n"
        
    with open(os.path.join(output_dir, "NOAA_Summary.txt"), "w") as f:
        f.write(summary)
        
    print("\n[+] Environmental generation complete!")