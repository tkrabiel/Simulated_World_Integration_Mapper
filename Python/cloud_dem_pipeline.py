import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.io import MemoryFile
import geopandas as gpd
from pystac_client import Client
import planetary_computer
import s3fs
from pathlib import Path

def get_chart_outline(db_dir: str, chart_name: str):
    """Fetches the M_COVR polygon for a specific chart from the master Parquet file."""
    parquet_file = Path(db_dir) / "M_COVR.parquet"
    if not parquet_file.exists(): return None
        
    master_gdf = gpd.read_parquet(parquet_file)
    # Check if CHART_NAME is a list (due to deduplication) or a string
    if isinstance(master_gdf['CHART_NAME'].iloc[0], list):
        chart_gdf = master_gdf[master_gdf['CHART_NAME'].apply(lambda x: chart_name in x)]
    else:
        chart_gdf = master_gdf[master_gdf['CHART_NAME'] == chart_name]
    
    if chart_gdf.empty: return None
    return chart_gdf.unary_union 

def build_chart_clipped_dem(chart_name, db_dir, tile_index_path, output_tiff):
    print(f"Loading chart outline for {chart_name}...")
    chart_outline = get_chart_outline(db_dir, chart_name)
    if chart_outline is None:
        print(f"Error: No M_COVR layer found for {chart_name}. Did you scrape it?")
        return

    bbox = chart_outline.bounds
    dem_datasets = []
    
    print("Querying USGS 3DEP STAC Catalog...")
    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    search = catalog.search(collections=["3dep-seamless"], bbox=bbox)
    for item in search.items():
        signed_item = planetary_computer.sign(item)
        dem_datasets.append(rasterio.open(signed_item.assets["data"].href))

    print("Querying NOAA BlueTopo S3 Bucket...")
    noaa_index = gpd.read_file(tile_index_path)
    intersecting_tiles = noaa_index.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    fs = s3fs.S3FileSystem(anon=True)
    
    for _, row in intersecting_tiles.iterrows():
        tile_name = row['TileName']
        s3_url = f"s3://noaa-ocs-nationalbathymetry-pds/BlueTopo/{tile_name}.tiff"
        if fs.exists(s3_url):
            dem_datasets.append(rasterio.open(s3_url))

    if not dem_datasets: return print("No DEMs found.")

    print(f"Merging {len(dem_datasets)} cloud tiles...")
    mosaic, out_transform = merge(dem_datasets, bounds=bbox)
    out_meta = dem_datasets[0].meta.copy()
    out_meta.update({"driver": "GTiff", "height": mosaic.shape[1], "width": mosaic.shape[2], "transform": out_transform, "count": 1, "nodata": 0.0})

    print("Clipping to outline...")
    with MemoryFile() as memfile:
        with memfile.open(**out_meta) as mem_ds:
            mem_ds.write(mosaic)
            clipped_arr, clipped_trans = mask(mem_ds, [chart_outline], crop=True, filled=True)
            clipped_meta = mem_ds.meta.copy()
            clipped_meta.update({"height": clipped_arr.shape[1], "width": clipped_arr.shape[2], "transform": clipped_trans})

    with rasterio.open(output_tiff, "w", **clipped_meta) as dest:
        dest.write(clipped_arr)
    for ds in dem_datasets: ds.close()
    print("Cloud DEM complete.")