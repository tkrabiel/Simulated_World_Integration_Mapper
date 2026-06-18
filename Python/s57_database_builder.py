import os
import zipfile
import urllib.request
import geopandas as gpd
import pandas as pd
from pathlib import Path
import warnings

# Mute Pandas FutureWarnings about concatenating empty columns
warnings.simplefilter(action='ignore', category=FutureWarning)

from s57_dictionaries import scale_band_dic

def get_chart_metadata(path):
    """Extracts Date and Scale metadata from the chart."""
    date, scale = "UNKNOWN", "UNKNOWN"
    try:
        dsid = gpd.read_file(path, layer='DSID')
        if not dsid.empty and 'ISDT' in dsid.columns: 
            date = str(dsid['ISDT'].iloc[0])
    except Exception: 
        pass
        
    chart_name = path.stem 
    if len(chart_name) >= 3:
        band_char = chart_name[2] 
        scale = scale_band_dic.get(band_char, "UNKNOWN")
        
    return date, scale

def build_database(charts_in_path, db_out_path, targets):
    """
    The core backend engine for extracting S-57 layers, performing spatial deduplication,
    and upserting/soft-deleting features into GeoParquet.
    """
    print("\n--- STARTING DB BUILD ---")
    
    if charts_in_path.startswith("http"):
        print("Downloading charts from URL...")
        os.makedirs(db_out_path, exist_ok=True)
        zip_path = Path(db_out_path) / "charts.zip"
        urllib.request.urlretrieve(charts_in_path, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as z: 
            z.extractall(db_out_path)
        os.remove(zip_path)
        charts_in_path = db_out_path

    chart_paths = list(Path(charts_in_path).rglob('*.000'))
    if not chart_paths:
        print("[!] No .000 files found in the provided directory.")
        return

    # Track specific charts processed during this run for smart delta-updates
    processed_chart_names = set([c.stem for c in chart_paths])
    
    for layer in targets:
        print(f"Processing {layer}...")
        layer_gdfs = []
        out_pq = Path(db_out_path) / f"{layer}.parquet"
        
        for chart in chart_paths:
            try:
                gdf = gpd.read_file(chart, layer=layer)
                if not gdf.empty:
                    date, scale = get_chart_metadata(chart)
                    gdf['CHART_NAME'] = chart.stem
                    gdf['CHART_DATE'] = date
                    gdf['CHART_SCALE'] = scale
                    layer_gdfs.append(gdf)
            except Exception: 
                pass # Layer doesn't exist in this specific chart
        
        if layer_gdfs:
            # Drop fully empty columns to mute Pandas warnings
            clean_gdfs = [gdf.dropna(axis=1, how='all') for gdf in layer_gdfs]
            master_gdf = pd.concat(clean_gdfs, ignore_index=True)
            
            master_gdf['geom_wkt'] = master_gdf.geometry.to_wkt()
            agg_funcs = {col: 'first' for col in master_gdf.columns if col not in ['CHART_NAME', 'CHART_DATE', 'CHART_SCALE', 'geom_wkt']}
            
            agg_funcs['CHART_NAME'] = lambda x: list(pd.Series(x).unique())
            agg_funcs['CHART_DATE'] = lambda x: list(pd.Series(x).unique())
            agg_funcs['CHART_SCALE'] = lambda x: list(pd.Series(x).unique())
            
            deduped_df = master_gdf.groupby('geom_wkt', as_index=False).agg(agg_funcs)
            final_gdf = gpd.GeoDataFrame(deduped_df, geometry='geometry', crs=layer_gdfs[0].crs)
            #To show the amount found and amount unique and duplicates
            print(f"    -> Scraped {len(master_gdf)} raw features. Deduplicated down to {len(final_gdf)} unique active features.")
            
            # Default status for brand new scraped data is ACTIVE
            final_gdf['STATUS'] = 'ACTIVE'

            # --- SMART UPSERT & SOFT DELETE LOGIC ---
            if out_pq.exists():
                print(f"[*] Found existing database for {layer}. Calculating updates...")
                old_gdf = gpd.read_parquet(out_pq)
                if 'STATUS' not in old_gdf.columns: 
                    old_gdf['STATUS'] = 'ACTIVE'
                
                new_wkts = set(final_gdf['geom_wkt'])
                old_wkts = set(old_gdf['geom_wkt'])
                missing_wkts = old_wkts - new_wkts
                
                # Determine if a missing feature was deleted from current charts or belongs to un-scanned charts
                def flag_removals(row):
                    if row['geom_wkt'] in missing_wkts:
                        old_charts = row['CHART_NAME']
                        if isinstance(old_charts, str): old_charts_set = {old_charts}
                        elif hasattr(old_charts, '__iter__'): old_charts_set = set(old_charts)
                        else: old_charts_set = {str(old_charts)}
                            
                        # If the feature belonged to the charts we are updating today, it has been removed
                        if old_charts_set.intersection(processed_chart_names):
                            return 'REMOVED'
                    return row.get('STATUS', 'ACTIVE')
                
                # Flag old items
                old_gdf['STATUS'] = old_gdf.apply(flag_removals, axis=1)
                
                # Strip out old data that is being updated with fresh new data, then merge the two together
                old_gdf_kept = old_gdf[~old_gdf['geom_wkt'].isin(new_wkts)]
                merged_df = pd.concat([old_gdf_kept, final_gdf], ignore_index=True)
                final_gdf = gpd.GeoDataFrame(merged_df, geometry='geometry', crs=layer_gdfs[0].crs)

            final_gdf.to_parquet(out_pq)
            print(f"[*] Saved {layer}.parquet. Total features tracked: {len(final_gdf)}")
        else:
            print(f"[-] No features found for {layer}.")
            
    print("--- DB BUILD COMPLETE ---")