import os
import numpy as np
import rasterio
from rasterio.features import rasterize
import geopandas as gpd
import pandas as pd
from PIL import Image
from pathlib import Path

def load_parquet_layer(db_dir: str, layer_name: str) -> gpd.GeoDataFrame:
    """Helper to load a single master parquet file for a specific layer."""
    parquet_file = Path(db_dir) / f"{layer_name}.parquet"
    if not parquet_file.exists(): return gpd.GeoDataFrame()
    return gpd.read_parquet(parquet_file)

def build_topobathy_dem(db_dir, bathy_dem_path, topo_dem_path, output_dem_path):
    print("Generating TopoBathy DEM...")
    
    # Extract Dredge & Land polygons from Parquet DB
    dredge_gdf = load_parquet_layer(db_dir, 'DRGARE')
    land_gdf = load_parquet_layer(db_dir, 'LNDARE')

    with rasterio.open(bathy_dem_path) as bathy_ds, rasterio.open(topo_dem_path) as topo_ds:
        meta = bathy_ds.meta.copy()
        bathy_arr = bathy_ds.read(1)
        topo_arr = topo_ds.read(1)
        out_shape = bathy_arr.shape
        transform = bathy_ds.transform

        # 1. Rasterize Dredge Areas
        dredge_mask = np.zeros(out_shape, dtype='float32')
        if not dredge_gdf.empty:
            shapes = ((geom, float(val)) for geom, val in zip(dredge_gdf.geometry, dredge_gdf['DRVAL1']) if pd.notna(val))
            dredge_mask = rasterize(shapes, out_shape=out_shape, transform=transform, fill=0, dtype='float32')
        
        bathy_arr = np.where(dredge_mask > 0, -abs(dredge_mask), bathy_arr)

        # 2. Rasterize Land Areas
        land_mask = np.zeros(out_shape, dtype='float32')
        if not land_gdf.empty:
            land_shapes = ((geom, 1) for geom in land_gdf.geometry)
            land_mask = rasterize(land_shapes, out_shape=out_shape, transform=transform, fill=0, dtype='float32')
            
        inverse_land_mask = np.where(land_mask == 1, 0, 1)

        # 3. Final Math: (Land Mask * Topo) + (Inverse Land Mask * Bathy)
        topobathy_arr = (land_mask * topo_arr) + (inverse_land_mask * bathy_arr)

        with rasterio.open(output_dem_path, 'w', **meta) as out_ds:
            out_ds.write(topobathy_arr.astype(meta['dtype']), 1)
            
    print(f"Saved TopoBathy DEM to {output_dem_path}")

def generate_terrain_ini(dem_path, output_dir):
    print("Generating terrain.ini and height.png...")
    
    with rasterio.open(dem_path) as ds:
        arr = ds.read(1)
        bounds = ds.bounds
        
        image_arr = arr[::-1, :]
        img_norm = ((image_arr - image_arr.min()) * (1/(image_arr.max() - image_arr.min()) * 255)).astype('uint8')
        img = Image.fromarray(img_norm)
        img.save(os.path.join(output_dir, "height.png"))
        
        we_dist = abs(bounds.right - bounds.left) * 111320
        sn_dist = abs(bounds.top - bounds.bottom) * 111320 

        with open(os.path.join(output_dir, "terrain.ini"), "w") as f:
            f.write(f'''Number=1
MapImage="texture.png"
HeightMap(1)="height.png"
Texture(1)="texture.png"
TerrainLong(1)={bounds.left:.4f}
TerrainLat(1)={bounds.bottom:.4f}
TerrainLongExtent(1)={we_dist:.3f}
TerrainLatExtent(1)={sn_dist:.3f}
TerrainMaxHeight(1)={abs(arr.max()):.1f}
SeaMaxDepth(1)={abs(arr.min()):.1f}
TerrainHeightMapSize(1)={img.height:.0f}
''')
    print("Terrain initialization complete.")