import os
import sys
import threading
import customtkinter as ctk
import tkintermapview
from tkinter import filedialog, messagebox
import geopandas as gpd
from pathlib import Path

# Import decoupled engine functionality
import noaa_environment_engine as engine

class PrintRedirector:
    def __init__(self, textbox): self.textbox = textbox
    def write(self, text): 
        self.textbox.insert(ctk.END, text)
        self.textbox.see(ctk.END)
    def flush(self): pass

class TideGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SWIM: Bridge Command Tide & Stream Builder")
        self.geometry("900x800")
        ctk.set_appearance_mode("dark")
        
        self.db_dir = ctk.StringVar()
        self.out_dir = ctk.StringVar()
        
        self.tide_stations = []
        self.current_stations = []
        self.covr_gdf = None
        
        self.build_ui()
        sys.stdout = PrintRedirector(self.console_output)

    def build_ui(self):
        ctk.CTkLabel(self, text="SWIM Tide & Stream Builder", font=("Arial", 22, "bold")).pack(pady=(15, 5))

        f1 = ctk.CTkFrame(self)
        f1.pack(fill="x", padx=20, pady=5)
        f1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f1, text="Database (GeoParquet):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.db_dir, placeholder_text="Where is M_COVR.parquet?").grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse_folder(self.db_dir)).grid(row=0, column=2, padx=10, pady=5)

        ctk.CTkLabel(f1, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(f1, textvariable=self.out_dir, placeholder_text="Where to save INIs & Summary...").grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(f1, text="Browse", width=60, command=lambda: self.browse_folder(self.out_dir)).grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkButton(self, text="1. Scan Map & Fetch NOAA Stations", fg_color="blue", command=lambda: threading.Thread(target=self.scan_and_fetch, daemon=True).start()).pack(fill="x", padx=20, pady=5)

        f2 = ctk.CTkFrame(self)
        f2.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.map_widget = tkintermapview.TkinterMapView(f2, corner_radius=0)
        self.map_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        f3 = ctk.CTkFrame(self)
        f3.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f3, text="Primary Tide Station (For tide.ini):").pack(side="left", padx=10)
        self.tide_combo = ctk.CTkComboBox(f3, width=300, values=["Scan map first..."])
        self.tide_combo.pack(side="left", padx=10)
        
        ctk.CTkButton(self, text="2. Generate Environmental INIs", fg_color="green", command=lambda: threading.Thread(target=self.run_generation, daemon=True).start()).pack(fill="x", padx=20, pady=10)

        self.console_output = ctk.CTkTextbox(self, height=150)
        self.console_output.pack(fill="both", padx=20, pady=(0, 20))

    def browse_folder(self, var):
        folder = filedialog.askdirectory()
        if folder: var.set(folder)

    def scan_and_fetch(self):
        db = self.db_dir.get().strip()
        if not db: return print("[!] Set Database path to find M_COVR.parquet.")
            
        covr_path = Path(db) / "M_COVR.parquet"
        if not covr_path.exists(): return print("[!] M_COVR.parquet not found in the specified directory.")
            
        print("\n[*] Reading M_COVR boundaries...")
        self.covr_gdf = gpd.read_parquet(covr_path)
        minx, miny, maxx, maxy = self.covr_gdf.total_bounds
        
        # UI Map Updates
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_polygon()
        self.map_widget.fit_bounding_box((maxy, minx), (miny, maxx))
        
        for geom in self.covr_gdf.geometry:
            if geom.geom_type == 'Polygon':
                self.map_widget.set_polygon([(y, x) for x, y in geom.exterior.coords], outline_color="red", border_width=2, fill_color="orange")
            elif geom.geom_type == 'MultiPolygon':
                for poly in geom.geoms:
                    self.map_widget.set_polygon([(y, x) for x, y in poly.exterior.coords], outline_color="red", border_width=2, fill_color="orange")

        print("[*] Contacting NOAA CO-OPS Servers...")
        try:
            all_tides = engine.fetch_stations("waterlevels")
            self.tide_stations = engine.filter_by_bounding_box(all_tides, miny, maxy, minx, maxx)
            
            all_currents = engine.fetch_stations("currentpredictions")
            self.current_stations = engine.filter_by_bounding_box(all_currents, miny, maxy, minx, maxx)
        except Exception as e:
            return print(f"[-] Connection failed: {e}")
            
        print(f"[+] Located {len(self.tide_stations)} Tide markers and {len(self.current_stations)} Current markers.")
        
        tide_options = []
        for s in self.tide_stations:
            name = s.get('name', 'Unknown')
            sid = s.get('id', '0000000')
            lat, lon = float(s.get('lat', 0)), float(s.get('lng', s.get('lon', 0)))
            tide_options.append(f"{sid} - {name}")
            self.map_widget.set_marker(lat, lon, text=f"TIDE: {name}", marker_color_circle="blue")
            
        for s in self.current_stations:
            name = s.get('name', 'Unknown')
            lat, lon = float(s.get('lat', 0)), float(s.get('lng', s.get('lon', 0)))
            self.map_widget.set_marker(lat, lon, text=f"CURRENT: {name}", marker_color_circle="green")
            
        if tide_options:
            self.tide_combo.configure(values=tide_options)
            self.tide_combo.set(tide_options[0])
        else:
            self.tide_combo.configure(values=["No tide stations found in area"])
            self.tide_combo.set("No tide stations found in area")

    def run_generation(self):
        out = self.out_dir.get().strip()
        selection = self.tide_combo.get()
        
        if not out: return print("[!] Please select an Output Directory.")
        if "No tide stations" in selection or not self.tide_stations: 
            return print("[!] Cannot build without a valid primary tide station record selection.")
            
        try:
            engine.build_environment_assets(out, selection, self.tide_stations, self.current_stations)
        except Exception as e:
            print(f"[-] Error processing assets: {e}")

if __name__ == "__main__":
    app = TideGUI()
    app.mainloop()