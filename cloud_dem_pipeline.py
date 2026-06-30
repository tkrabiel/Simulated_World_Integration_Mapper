import os
import re
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.io import MemoryFile
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from pystac_client import Client
import planetary_computer
from PIL import Image
from pathlib import Path
from shapely.geometry import Polygon

# CRITICAL: This allows GDAL/Rasterio to anonymously stream from public AWS S3 buckets for USGS.
os.environ["AWS_NO_SIGN_REQUEST"] = "YES"

def get_squared_bounds(db_dir: str):
    """Fetches M_COVR bounds and squares them off based on the longest axis."""
    parquet_file = Path(db_dir) / "M_COVR.parquet"
    if not parquet_file.exists(): return None
    covr_gdf = gpd.read_parquet(parquet_file)
    if covr_gdf.empty: return None
    
    minx, miny, maxx, maxy = covr_gdf.total_bounds
    dx = maxx - minx
    dy = maxy - miny
    max_dim = max(dx, dy)
    
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    return [cx - max_dim / 2, cy - max_dim / 2, cx + max_dim / 2, cy + max_dim / 2]

def warp_to_4326(src, dst_crs="EPSG:4326", resolution=0.00009, output_path=None):
    """Warps a raster into EPSG:4326. If output_path is provided, saves to disk to save RAM."""
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds, resolution=resolution
    )
    kwargs = src.meta.copy()
    kwargs.update({'crs': dst_crs, 'transform': transform, 'width': width, 'height': height, 'nodata': np.nan})

    if output_path:
        with rasterio.open(output_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform, src_crs=src.crs,
                    dst_transform=transform, dst_crs=dst_crs,
                    resampling=Resampling.bilinear
                )
        return output_path
    else:
        memfile = MemoryFile()
        dst = memfile.open(**kwargs)
        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=rasterio.band(dst, i),
                src_transform=src.transform, src_crs=src.crs,
                dst_transform=transform, dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )
        return dst, memfile

def apply_color_gradient(dem_array):
    """Applies a realistic geographic colormap to the elevation data."""
    h, w = dem_array.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    bins = [-10000, -50, 0, 5, 500, 2000, 10000]
    colors = [
        [0, 20, 80],      # Dark Blue
        [60, 140, 200],   # Light Blue
        [210, 180, 140],  # Sand
        [34, 139, 34],    # Forest Green
        [139, 69, 19],    # Brown
        [255, 255, 255]   # Snow White
    ]
    rgb[dem_array <= bins[1]] = colors[0]
    rgb[(dem_array > bins[1]) & (dem_array <= bins[2])] = colors[1]
    rgb[(dem_array > bins[2]) & (dem_array <= bins[3])] = colors[2]
    rgb[(dem_array > bins[3]) & (dem_array <= bins[4])] = colors[3]
    rgb[(dem_array > bins[4]) & (dem_array <= bins[5])] = colors[4]
    rgb[dem_array > bins[5]] = colors[5]
    return rgb

def update_landobject_ini(ini_path, dem_array, transform):
    """Parses an existing landobject.ini and snaps object heights to the DEM terrain surface."""
    if not os.path.exists(ini_path):
        return print(f"[-] landobject.ini not found at {ini_path}. Skipping height injection.")
        
    print(f"\n[*] Snapping Land Objects to Terrain Surface...")
    with open(ini_path, 'r') as f:
        lines = f.readlines()
        
    objects = {}
    total_objects = 0
    pattern = re.compile(r"([A-Za-z]+)\((\d+)\)=(.*)")
    
    for line in lines:
        line = line.strip()
        if line.startswith("Number="):
            total_objects = int(line.split("=")[1])
            continue
            
        match = pattern.match(line)
        if match:
            key, idx, val = match.groups()
            idx = int(idx)
            if idx not in objects:
                objects[idx] = {}
            objects[idx][key] = val.strip().strip('"') 
            
    h, w = dem_array.shape
    updated_count = 0
    
    for idx, obj in objects.items():
        if 'Lat' in obj and 'Long' in obj:
            lat = float(obj['Lat'])
            lon = float(obj['Long'])
            
            # Translate Lat/Long into Pixel Coordinates (Row/Col) using the raster's affine transform
            col, row = ~transform * (lon, lat)
            col, row = int(col), int(row)
            
            z = 0.0
            if 0 <= row < h and 0 <= col < w:
                z = dem_array[row, col]
                if np.isnan(z):
                    z = 0.0
            
            # Snap to ground: Base Height + Raster Elevation
            existing_hc = float(obj.get('HeightCorrection', 0.0))
            obj['HeightCorrection'] = existing_hc + z
            
            # Enforce Simulator Overrides
            obj['Absolute'] = 1
            obj['Collision'] = 1
            obj['Radar'] = 1
            updated_count += 1
            
    # Rewrite the modified file
    with open(ini_path, 'w') as f:
        f.write(f"Number={total_objects}\n\n")
        for idx in sorted(objects.keys()):
            obj = objects[idx]
            f.write(f'Type({idx})="{obj.get("Type", "unknown")}"\n')
            f.write(f'Lat({idx})={obj["Lat"]}\n')
            f.write(f'Long({idx})={obj["Long"]}\n')
            
            rot = obj.get("Rotation")
            if rot is not None:
                f.write(f'Rotation({idx})={rot}\n')
                
            f.write(f'HeightCorrection({idx})={obj["HeightCorrection"]:.2f}\n')
            f.write(f'Absolute({idx})=1\n')
            f.write(f'Collision({idx})=1\n')
            f.write(f'Radar({idx})=1\n\n')
            
    print(f"    -> Mathematically snapped {updated_count} land objects to the DEM surface.")

def build_terrain_assets(db_dir, output_dir, local_noaa_gpkg=None, local_noaa_tiles_dir=None, landobject_ini_path=None):
    print("\n--- STARTING DEM GENERATION ---")
    bounds = get_squared_bounds(db_dir)
    if bounds is None: return print("[!] No M_COVR data found.")

    minx, miny, maxx, maxy = bounds
    target_res = 0.00009
    width = int((maxx - minx) / target_res)
    height = int((maxy - miny) / target_res)
    out_shape = (height, width)
    topo_transform = from_bounds(minx, miny, maxx, maxy, width, height)

    topo_dataset_paths = []
    bathy_dataset_paths = []

    usgs_cache_dir = os.path.join(output_dir, "USGS_Topo_Cache")
    os.makedirs(usgs_cache_dir, exist_ok=True)
    
    if not local_noaa_tiles_dir:
        local_noaa_tiles_dir = os.path.join(output_dir, "NOAA_BlueTopo_Cache")
    os.makedirs(local_noaa_tiles_dir, exist_ok=True)

    # 1. Fetch USGS 3DEP Topography
    print("\n[*] Querying USGS 3DEP STAC Catalog for Land Topography...")
    try:
        catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
        search = catalog.search(collections=["3dep-seamless"], bbox=bounds)
        items = list(search.items())
        
        if items:
            total_usgs = len(items)
            print(f"[*] Found {total_usgs} USGS Topo tiles.")
            for i, item in enumerate(items, start=1):
                tile_id = item.id
                print(f"    -> Processing USGS Tile [{i}/{total_usgs}]: {tile_id}...")
                
                cache_path = os.path.join(usgs_cache_dir, f"{tile_id}_warped.tif")
                if not os.path.exists(cache_path):
                    href = planetary_computer.sign(item).assets["data"].href
                    with rasterio.open(href) as src:
                        if src.crs.to_string() != "EPSG:4326":
                            warp_to_4326(src, output_path=cache_path)
                        else:
                            with rasterio.open(cache_path, 'w', **src.meta) as dest:
                                dest.write(src.read())
                topo_dataset_paths.append(cache_path)
    except Exception as e: print(f"[-] USGS Topo fetch failed: {e}")

    # 2. Fetch NOAA BlueTopo Bathymetry (Using Official NOAA API)
    print("\n[*] Querying NOAA BlueTopo via Official API...")
    try:
        from nbs.noaabathymetry import fetch_tiles
        
        bounds_poly = box(minx, miny, maxx, maxy)
        bounds_gdf = gpd.GeoDataFrame({'geometry': [bounds_poly]}, crs="EPSG:4326")
        geom_path = os.path.join(local_noaa_tiles_dir, "search_bounds.gpkg")
        bounds_gdf.to_file(geom_path, driver="GPKG")
        
        print(f"    -> Handing search bounds to NOAA API. Syncing tiles to {local_noaa_tiles_dir}...")
        fetch_tiles(local_noaa_tiles_dir, geometry=geom_path)
        
        downloaded_tiffs = list(Path(local_noaa_tiles_dir).rglob("*.tiff")) + list(Path(local_noaa_tiles_dir).rglob("*.tif"))
        raw_tiffs = [f for f in downloaded_tiffs if "_warped" not in f.name]
        
        if not raw_tiffs:
            print("[-] No NOAA tiles were found for this region by the API.")
        else:
            print(f"[*] Found {len(raw_tiffs)} local NOAA tiles downloaded by API.")
            for i, tiff_path in enumerate(raw_tiffs, start=1):
                tile_name = tiff_path.stem
                print(f"    -> Processing NOAA Tile [{i}/{len(raw_tiffs)}]: {tile_name}...")
                
                warped_cache_path = os.path.join(local_noaa_tiles_dir, f"{tile_name}_warped.tif")
                if not os.path.exists(warped_cache_path):
                    try:
                        with rasterio.open(tiff_path) as src:
                            warp_to_4326(src, output_path=warped_cache_path)
                    except Exception as e:
                        print(f"       [!] Warning: Failed to process local {tiff_path.name}. {e}")
                        continue
                bathy_dataset_paths.append(warped_cache_path)
    except ImportError:
        print("[-] ERROR: 'nbs.noaabathymetry' package is not installed in this Python environment.")
    except Exception as e: 
        print(f"[-] NOAA BlueTopo API fetch failed: {e}")

    # 3. Create Base Arrays (Lazy Loading from Disk)
    print("\n[*] Structuring Base Arrays (Merging from Disk)...")
    if topo_dataset_paths:
        topo_arr = merge(topo_dataset_paths, bounds=bounds, res=target_res, nodata=np.nan)[0][0]
        topo_arr[topo_arr <= 0] = np.nan
    else:
        topo_arr = np.full(out_shape, np.nan, dtype='float32')

    if bathy_dataset_paths:
        bathy_arr = merge(bathy_dataset_paths, bounds=bounds, res=target_res, nodata=np.nan)[0][0]
    else:
        bathy_arr = np.full(out_shape, np.nan, dtype='float32')

    # 4. NOAA-Primary Masking Logic
    print("    -> Masking USGS Topography with NOAA Bathymetry...")
    noaa_valid_mask = ~np.isnan(bathy_arr)
    topo_arr[noaa_valid_mask] = np.nan
    final_dem = np.where(noaa_valid_mask, bathy_arr, topo_arr)
    final_dem = np.nan_to_num(final_dem, nan=0.0)

    # 5. Optional Vector Override (DRGARE)
    # 5. Optional Vector Override (DRGARE)
    dredge_file = Path(db_dir) / "DRGARE.parquet"
    if dredge_file.exists():
        try:
            dredge_gdf = gpd.read_parquet(dredge_file)
            if not dredge_gdf.empty:
                print("    -> Burning DRGARE (Dredged Areas) over DEM...")

                # FIX: Force the mask to strictly match the exact shape Rasterio generated
                actual_shape = final_dem.shape

                shapes = ((geom, float(val)) for geom, val in zip(dredge_gdf.geometry, dredge_gdf['DRVAL1']) if
                          pd.notna(val))
                dredge_mask = rasterize(shapes, out_shape=actual_shape, transform=topo_transform, fill=0,
                                        dtype='float32')
                final_dem = np.where(dredge_mask > 0, -abs(dredge_mask), final_dem)

        except Exception as e:
            print(
                f"       [!] Warning: Failed to apply DRGARE dredge depths. Skipping dredge override and moving on. Reason: {e}")

    z_min, z_max = final_dem.min(), final_dem.max()

    # 6. Inject Heights into Land Objects INI
    if landobject_ini_path:
        update_landobject_ini(landobject_ini_path, final_dem, topo_transform)

    # 7. Generate Simulator Assets
    print(f"\n[*] Generating Simulator Maps & Textures...")
    try:
        img_tex = Image.fromarray(apply_color_gradient(final_dem)).resize((1024, 1024), resample=Image.Resampling.BILINEAR)
        img_tex.save(os.path.join(output_dir, "texture.png"))

        img_preview = Image.fromarray(((final_dem - z_min) / (z_max - z_min) * 255).astype(np.uint8)).resize((1025, 1025), resample=Image.Resampling.BILINEAR)
        img_preview.save(os.path.join(output_dir, "height_preview.png"))

        img_f32 = Image.fromarray(final_dem, mode='F').resize((1025, 1025), resample=Image.Resampling.BILINEAR)
        np.array(img_f32, dtype=np.float32).tofile(os.path.join(output_dir, "height.f32"))

        with open(os.path.join(output_dir, "terrain.ini"), "w") as f:
            f.write(f'Number=1\n\nMapImage="texture.png"\n\nHeightMap(1)="height.f32"\nTexture(1)="texture.png"\nTerrainLong(1)={minx:.6f}\nTerrainLat(1)={miny:.6f}\nTerrainLongExtent(1)={abs(maxx - minx):.6f}\nTerrainLatExtent(1)={abs(maxy - miny):.6f}\nTerrainMaxHeight(1)={abs(z_max):.2f}\nSeaMaxDepth(1)={abs(z_min):.2f}\nTerrainHeightMapSize(1)=1025\nTerrainHeightMapRows(1)=1025\nTerrainHeightMapColumns(1)=1025\nUsesRGB(1)=0\n')
    except Exception as e:
        print(f"[-] ERROR saving Bridge Command final assets: {e}")

    print("\n--- TERRAIN BUILD COMPLETE ---")