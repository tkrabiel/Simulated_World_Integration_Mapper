import os
import geopandas as gpd
import pandas as pd
from pathlib import Path
import math
from s57_dictionaries import boyshp_dic, catcam_dic, bcnshp_dic, colour_builder, colour_dic, parse_light_sequence, get_rgb

def load_parquet_layer(db_dir: str, layer_name: str) -> gpd.GeoDataFrame:
    """Helper to load a single master parquet file for a specific layer."""
    parquet_file = Path(db_dir) / f"{layer_name}.parquet"
    if not parquet_file.exists(): return gpd.GeoDataFrame()
    return gpd.read_parquet(parquet_file)

def generate_buoy_ini(db_dir, ini_path):
    print("Generating Buoy INI...")
    layers = ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP']
    gdfs = [load_parquet_layer(db_dir, l) for l in layers]
    buoys = pd.concat([gdf for gdf in gdfs if not gdf.empty], ignore_index=True) if gdfs else gpd.GeoDataFrame()
    
    if buoys.empty:
        print("No buoys found in database.")
        return

    os.makedirs(ini_path, exist_ok=True)
    total_count = len(buoys)
    
    with open(os.path.join(ini_path, "buoy.ini"), "w") as f:
        f.write(f"Number={total_count}\n")
        
        # itertuples() is lightning fast and doesn't crash on geometries
        for count, row in enumerate(buoys.itertuples()):
            # getattr is used safely in case a column is entirely missing from the parquet file
            boyshp_raw = getattr(row, 'BOYSHP', '')
            catcam_raw = getattr(row, 'CATCAM', '')
            colour_raw = getattr(row, 'COLOUR', '')
            
            boyshp = boyshp_dic.get(str(boyshp_raw).replace('.0', ''), "unknown")
            catcam = str(catcam_raw).replace('.0', '')
            
            if pd.notna(catcam_raw) and catcam in catcam_dic:
                buoy_type = f"{boyshp}_{catcam_dic[catcam]}"
            else:
                buoy_type = f"{boyshp}_{colour_builder(colour_raw)}"
                
            f.write(f'Type({count})="{buoy_type}"\nLAT({count})={row.geometry.y}\nLONG({count})={row.geometry.x}\n\n')
            
    print(f"Buoy INI generated with {total_count} features.")

def generate_bcn_ini(db_dir, ini_path):
    print("Generating Beacon INI...")
    layers = ['BCNLAT', 'BCNCAR', 'BCNISD', 'BCNSAW', 'BCNSPP']
    gdfs = [load_parquet_layer(db_dir, l) for l in layers]
    bcns = pd.concat([gdf for gdf in gdfs if not gdf.empty], ignore_index=True) if gdfs else gpd.GeoDataFrame()

    if bcns.empty:
        print("No beacons found in database.")
        return

    os.makedirs(ini_path, exist_ok=True)
    total_count = len(bcns)
    
    with open(os.path.join(ini_path, "bcn.ini"), "w") as f:
        f.write(f"Number={total_count}\n")
        
        for count, row in enumerate(bcns.itertuples()):
            bcnshp_raw = getattr(row, 'BCNSHP', '')
            colour_raw = getattr(row, 'COLOUR', '')
            
            bcnshp = bcnshp_dic.get(str(bcnshp_raw).replace('.0', ''), "unknown")
            bcn_type = f"{bcnshp}_{colour_builder(colour_raw)}"
            
            f.write(f'Type({count})="{bcn_type}"\nLAT({count})={row.geometry.y}\nLONG({count})={row.geometry.x}\n\n')
            
    print(f"Beacon INI generated with {total_count} features.")

def generate_light_ini(db_dir, ini_path, height_eye=15):
    print("Generating Light INI...")
    lights = load_parquet_layer(db_dir, 'LIGHTS')
    
    if lights.empty:
        print("No lights found in database.")
        return

    os.makedirs(ini_path, exist_ok=True)
    total_count = len(lights)
    
    with open(os.path.join(ini_path, "light.ini"), "w") as f:
        f.write(f"Number={total_count}\n")
        
        for count, row in enumerate(lights.itertuples(), start=1):
            colour_raw = getattr(row, 'COLOUR', '')
            sigseq_raw = getattr(row, 'SIGSEQ', '')
            sectr1_raw = getattr(row, 'SECTR1', '0')
            sectr2_raw = getattr(row, 'SECTR2', '360')
            height_raw = getattr(row, 'HEIGHT', 3.5)
            
            color_key = str(colour_raw).replace('.0', '')
            colour = colour_dic.get(color_key, "white")
            r, g, b = get_rgb(colour.split('_')[0] if '_' in colour else colour)
            
            sequence = parse_light_sequence(sigseq_raw)
            start_angle = str(sectr1_raw).replace('.0', '')
            end_angle = str(sectr2_raw).replace('.0', '')
            
            height = float(height_raw) if pd.notna(height_raw) and str(height_raw).strip() != '' else 3.5
            range_light = int(round(1.17 * (math.sqrt(height * 3.3) + math.sqrt(height_eye * 3.3))))
            
            f.write(f'Lat({count})={row.geometry.y}\nLong({count})={row.geometry.x}\nHeight({count})={height}\n')
            f.write(f'Red({count})={r}\nGreen({count})={g}\nBlue({count})={b}\nRange({count})={range_light}\n')
            f.write(f'Sequence({count})="{sequence}"\nStartAngle({count})={start_angle}\nEndAngle({count})={end_angle}\n\n')
            
    print(f"Light INI generated with {total_count} features.")