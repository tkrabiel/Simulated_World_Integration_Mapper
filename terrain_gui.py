import sys
import threading
import customtkinter as ctk
import tkintermapview
from tkinter import filedialog, messagebox
import geopandas as gpd
from pathlib import Path
from cloud_dem_pipeline import build_terrain_assets

class PrintRedirector:
    def __init__(self, textbox): self.textbox = textbox
    def write(self, text): 
        self.textbox.insert(ctk.END, text)
        self.textbox.see(ctk.END)
    def flush(self): pass

class TerrainGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SWIM: Bridge Command Terrain Builder")
        self.geometry("680x580")
        ctk.set_appearance_mode("dark")
        
        self.db_dir = ctk.StringVar()
        self.out_dir = ctk.StringVar()
        self.noaa_gpkg = ctk.StringVar()
        self.noaa_tiles_dir = ctk.StringVar()
        self.landobject_ini = ctk.StringVar()
        
        self.build_ui()
        sys.stdout = PrintRedirector(self.console_output)

    def build_ui(self):
        ctk.CTkLabel(self, text="SWIM Terrain Builder", font=("Arial", 22, "bold")).pack(pady=(15, 10))

        f1 = ctk.CTkFrame(self)
        f1.pack(fill="x", padx=20, pady=5)
        f1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f1, text="Database (GeoParquet):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.db_dir, placeholder_text="Where is M_COVR.parquet?").grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse_folder(self.db_dir)).grid(row=0, column=2, padx=10, pady=5)

        ctk.CTkLabel(f1, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.out_dir, placeholder_text="Where to save f32/INIs?").grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse_folder(self.out_dir)).grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkLabel(f1, text="Local BlueTopo GPKG (Opt):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.noaa_gpkg, placeholder_text="Skip S3 search...").grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse_file(self.noaa_gpkg, "GeoPackage", "*.gpkg")).grid(row=2, column=2, padx=10, pady=5)

        ctk.CTkLabel(f1, text="Local NOAA Tiles Folder (Opt):").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.noaa_tiles_dir, placeholder_text="Local TIFF cache folder...").grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse_folder(self.noaa_tiles_dir)).grid(row=3, column=2, padx=10, pady=5)

        # NEW: Inject into landobject.ini
        ctk.CTkLabel(f1, text="LandObject INI File (Opt):").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.landobject_ini, placeholder_text="landobject.ini to snap to DEM...").grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse_file(self.landobject_ini, "INI File", "*.ini")).grid(row=4, column=2, padx=10, pady=5)

        self.btn_build = ctk.CTkButton(self, text="Build TopoBathy Terrain", fg_color="blue", command=lambda: threading.Thread(target=self.trigger_build, daemon=True).start())
        self.btn_build.pack(fill="x", padx=20, pady=15)

        self.console_output = ctk.CTkTextbox(self, height=200)
        self.console_output.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def browse_folder(self, var):
        folder = filedialog.askdirectory()
        if folder: var.set(folder)

    def browse_file(self, var, file_type, extension):
        filepath = filedialog.askopenfilename(filetypes=[(file_type, extension)])
        if filepath: var.set(filepath)

    def check_mcovr_connectivity(self, db_dir):
        covr_path = Path(db_dir) / "M_COVR.parquet"
        if not covr_path.exists():
            return True, None
        gdf = gpd.read_parquet(covr_path)
        if gdf.empty:
            return True, None
        
        metric_gdf = gdf.to_crs(epsg=3857)
        union_geom = metric_gdf.geometry.buffer(1.0).unary_union
        
        is_connected = union_geom.geom_type == 'Polygon'
        return is_connected, gdf

    def show_mcovr_map(self, gdf):
        map_win = ctk.CTkToplevel(self)
        map_win.title("WARNING: Disconnected Charts Detected")
        map_win.geometry("800x600")
        map_win.grab_set()

        ctk.CTkLabel(map_win, text="WARNING: Your M_COVR chart areas are disconnected!\nAn incomplete simulation will be generated.", text_color="red", font=("Arial", 16, "bold")).pack(pady=10)

        map_widget = tkintermapview.TkinterMapView(map_win, width=800, height=500, corner_radius=0)
        map_widget.pack(fill="both", expand=True)

        for geom in gdf.geometry:
            if geom.geom_type == 'Polygon':
                path = [(y, x) for x, y in geom.exterior.coords]
                map_widget.set_polygon(path, outline_color="red", border_width=2, fill_color="orange")
            elif geom.geom_type == 'MultiPolygon':
                for poly in geom.geoms:
                    path = [(y, x) for x, y in poly.exterior.coords]
                    map_widget.set_polygon(path, outline_color="red", border_width=2, fill_color="orange")

        minx, miny, maxx, maxy = gdf.total_bounds
        map_widget.fit_bounding_box((maxy, minx), (miny, maxx))

    def trigger_build(self):
        db = self.db_dir.get().strip()
        out = self.out_dir.get().strip()
        gpkg = self.noaa_gpkg.get().strip()
        tiles_dir = self.noaa_tiles_dir.get().strip()
        ini_path = self.landobject_ini.get().strip()
        
        if not db or not out:
            return print("[!] Set both Database and Output paths.")
            
        is_connected, covr_gdf = self.check_mcovr_connectivity(db)
        if not is_connected:
            messagebox.showwarning("Disconnected Charts", "Warning: Some of your M_COVR chart areas are not connected. An incomplete simulation will be made. See the map viewer for details.")
            self.after(0, self.show_mcovr_map, covr_gdf)
        
        build_terrain_assets(db, out, local_noaa_gpkg=gpkg, local_noaa_tiles_dir=tiles_dir, landobject_ini_path=ini_path)

if __name__ == "__main__":
    app = TerrainGUI()
    app.mainloop()