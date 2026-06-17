import os
import sys
import threading
import zipfile
import urllib.request
import geopandas as gpd
import pandas as pd
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog
import warnings

# Mute Pandas FutureWarnings about concatenating empty columns
warnings.simplefilter(action='ignore', category=FutureWarning)

# Import dictionaries and vector logic
from s57_dictionaries import scale_band_dic
from s57_vector_pipeline import generate_buoy_ini, generate_bcn_ini, generate_light_ini

LAYER_GROUPS = {
    "Lights": ['LIGHTS'],
    "Buoys": ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP'],
    "Daymarks/Beacons": ['BCNLAT', 'BCNCAR', 'BCNISD', 'BCNSAW', 'BCNSPP'],
    "Land/Dredge/Soundings": ['LNDARE', 'DRGARE', 'SOUNDG'],
    "Chart Outline (M_COVR)": ['M_COVR']
}

class PrintRedirector:
    def __init__(self, textbox): self.textbox = textbox
    def write(self, text): 
        self.textbox.insert(ctk.END, text)
        self.textbox.see(ctk.END)
    def flush(self): pass

class SwimMasterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SWIM: Bridge Command World Builder")
        self.geometry("800x700")
        ctk.set_appearance_mode("dark")
        
        self.charts_input = ctk.StringVar()
        self.db_dir = ctk.StringVar()
        self.ini_dir = ctk.StringVar()
        self.checkbox_vars = {}
        
        self.build_ui()
        sys.stdout = PrintRedirector(self.console_output)

    def build_ui(self):
        ctk.CTkLabel(self, text="SWIM Pipeline", font=("Arial", 24, "bold")).pack(pady=(15, 5))

        f1 = ctk.CTkFrame(self)
        f1.pack(fill="x", padx=20, pady=5)
        f1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f1, text="Charts Link/Folder:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.charts_input, placeholder_text="URL or local path...").grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse(self.charts_input)).grid(row=0, column=2, padx=10, pady=5)

        ctk.CTkLabel(f1, text="Database (GeoParquet):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.db_dir).grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse(self.db_dir)).grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkLabel(f1, text="Output INI Folder:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.ini_dir).grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse(self.ini_dir)).grid(row=2, column=2, padx=10, pady=5)

        f2 = ctk.CTkFrame(self)
        f2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f2, text="Scrape Features:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        col, row = 0, 1
        for group in LAYER_GROUPS.keys():
            var = ctk.BooleanVar(value=True)
            self.checkbox_vars[group] = var
            ctk.CTkCheckBox(f2, text=group, variable=var).grid(row=row, column=col, padx=10, pady=5, sticky="w")
            col += 1
            if col > 2: col, row = 0, row + 1

        f3 = ctk.CTkFrame(self, fg_color="transparent")
        f3.pack(fill="x", padx=20, pady=10)
        
        self.btn_db = ctk.CTkButton(f3, text="1. Build Database", command=lambda: self.run_thread(self.build_db))
        self.btn_db.pack(side="left", expand=True, padx=5)

        self.btn_ini = ctk.CTkButton(f3, text="2. Generate Bridge Command INIs", fg_color="green", command=lambda: self.run_thread(self.build_inis))
        self.btn_ini.pack(side="left", expand=True, padx=5)

        self.console_output = ctk.CTkTextbox(self, height=200)
        self.console_output.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def browse(self, var):
        folder = filedialog.askdirectory()
        if folder: var.set(folder)

    def run_thread(self, target):
        threading.Thread(target=target, daemon=True).start()

    def get_chart_metadata(self, path):
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

    def build_db(self):
        print("\n--- STARTING DB BUILD ---")
        charts_in = self.charts_input.get().strip()
        db_out = self.db_dir.get().strip()
        
        if not charts_in or not db_out: 
            return print("[!] Set Charts and DB paths.")
        
        if charts_in.startswith("http"):
            print("Downloading...")
            os.makedirs(db_out, exist_ok=True)
            zip_path = Path(db_out) / "charts.zip"
            urllib.request.urlretrieve(charts_in, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(db_out)
            os.remove(zip_path)
            charts_in = db_out

        targets = [l for g, v in self.checkbox_vars.items() if v.get() for l in LAYER_GROUPS[g]]
        chart_paths = list(Path(charts_in).rglob('*.000'))
        
        for layer in targets:
            print(f"Processing {layer}...")
            layer_gdfs = []
            out_pq = Path(db_out) / f"{layer}.parquet"
            
            for chart in chart_paths:
                try:
                    gdf = gpd.read_file(chart, layer=layer)
                    if not gdf.empty:
                        date, scale = self.get_chart_metadata(chart)
                        gdf['CHART_NAME'] = chart.stem
                        gdf['CHART_DATE'] = date
                        gdf['CHART_SCALE'] = scale
                        layer_gdfs.append(gdf)
                except Exception: 
                    pass
            
            if layer_gdfs:
                master_gdf = pd.concat(layer_gdfs, ignore_index=True)
                
                master_gdf['geom_wkt'] = master_gdf.geometry.to_wkt()
                agg_funcs = {col: 'first' for col in master_gdf.columns if col not in ['CHART_NAME', 'CHART_DATE', 'CHART_SCALE', 'geom_wkt']}
                
                agg_funcs['CHART_NAME'] = lambda x: list(pd.Series(x).unique())
                agg_funcs['CHART_DATE'] = lambda x: list(pd.Series(x).unique())
                agg_funcs['CHART_SCALE'] = lambda x: list(pd.Series(x).unique())
                
                deduped_df = master_gdf.groupby('geom_wkt', as_index=False).agg(agg_funcs)
                final_gdf = gpd.GeoDataFrame(deduped_df, geometry='geometry', crs=layer_gdfs[0].crs)
                
                final_gdf.to_parquet(out_pq)
                print(f"[*] Saved {layer}.parquet. Deduplicated {len(master_gdf)} down to {len(final_gdf)} unique features.")
            else:
                print(f"[-] No features found for {layer}.")
                
        print("--- DB BUILD COMPLETE ---")

    def build_inis(self):
        print("\n--- STARTING INI GENERATION ---")
        db_out = self.db_dir.get().strip()
        ini_out = self.ini_dir.get().strip()
        
        if not db_out or not ini_out: return print("[!] Set DB and INI paths.")
        
        generate_buoy_ini(db_out, ini_out)
        generate_bcn_ini(db_out, ini_out)
        generate_light_ini(db_out, ini_out)
        print("--- INI GENERATION COMPLETE ---")

if __name__ == "__main__":
    app = SwimMasterGUI()
    app.mainloop()