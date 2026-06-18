import os
import sys
import threading
import zipfile
import urllib.request
import geopandas as gpd
import pandas as pd
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import warnings

# Mute Pandas FutureWarnings about concatenating empty columns
warnings.simplefilter(action='ignore', category=FutureWarning)

# Import our backend engines
from s57_database_builder import build_database
from s57_vector_pipeline import generate_buoy_ini, generate_bcn_ini, generate_light_ini

LAYER_GROUPS = {
    "Lights": ['LIGHTS'],
    "Buoys": ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP'],
    "Daymarks/Beacons": ['BCNLAT', 'BCNCAR', 'BCNISD', 'BCNSAW', 'BCNSPP'],
    "Land Area": ['LNDARE'],
    "Dredge Area": ['DRGARE'],
    "Soundings": ['SOUNDG'],
    "Piers & Shoreline": ['SLCONS', 'PONTON'],
    "Coastline": ['COALNE'],
    "Berths": ['BERTHS'],
    "Obstructions": ['OBSTRN'],
    "Underwater Rocks": ['UWTROC'],
    "Wrecks": ['WRECKS'],
    "Unsurveyed Area": ['UNSARE'],
    "Chart Outline (M_COVR)": ['M_COVR']
}

class PrintRedirector:
    """Catches all print() statements from backend scripts and routes them to the GUI console."""
    def __init__(self, textbox): self.textbox = textbox
    def write(self, text): 
        self.textbox.insert(ctk.END, text)
        self.textbox.see(ctk.END)
    def flush(self): pass

class SwimMasterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SWIM: Bridge Command World Builder")
        self.geometry("850x800")
        ctk.set_appearance_mode("dark")
        
        self.charts_input = ctk.StringVar()
        self.db_dir = ctk.StringVar()
        self.ini_dir = ctk.StringVar()
        self.checkbox_vars = {}
        
        self.custom_targets = []
        self.custom_targets_label_var = ctk.StringVar(value="Custom Features Loaded: None")
        
        self.build_ui()
        sys.stdout = PrintRedirector(self.console_output)

    def build_ui(self):
        ctk.CTkLabel(self, text="SWIM Pipeline", font=("Arial", 24, "bold")).pack(pady=(15, 5))

        # --- PATHS ---
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

        # --- PRESET SCRAPER OPTIONS ---
        f2 = ctk.CTkFrame(self)
        f2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f2, text="Standard Features:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        col, row = 0, 1
        for group in LAYER_GROUPS.keys():
            var = ctk.BooleanVar(value=True)
            self.checkbox_vars[group] = var
            ctk.CTkCheckBox(f2, text=group, variable=var).grid(row=row, column=col, padx=10, pady=5, sticky="w")
            col += 1
            if col > 3: col, row = 0, row + 1

        # --- CUSTOM JSON OPTIONS ---
        f_custom = ctk.CTkFrame(self)
        f_custom.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(f_custom, text="Advanced JSON Features:", font=("Arial", 12, "bold")).pack(side="left", padx=10, pady=5)
        
        btn_build_json = ctk.CTkButton(f_custom, text="Build Custom JSON", width=120, command=self.open_json_builder)
        btn_build_json.pack(side="left", padx=5, pady=5)
        
        btn_load_json = ctk.CTkButton(f_custom, text="Load Custom JSON", width=120, command=self.load_custom_json)
        btn_load_json.pack(side="left", padx=5, pady=5)
        
        lbl_loaded = ctk.CTkLabel(f_custom, textvariable=self.custom_targets_label_var, font=("Arial", 10, "italic"))
        lbl_loaded.pack(side="right", padx=10)

        # --- BUTTONS ---
        f3 = ctk.CTkFrame(self, fg_color="transparent")
        f3.pack(fill="x", padx=20, pady=10)
        
        self.btn_db = ctk.CTkButton(f3, text="1. Build Database", command=lambda: self.run_thread(self.trigger_db_build))
        self.btn_db.pack(side="left", expand=True, padx=5)

        self.btn_ini = ctk.CTkButton(f3, text="2. Generate Bridge Command INIs", fg_color="green", command=lambda: self.run_thread(self.trigger_ini_build))
        self.btn_ini.pack(side="left", expand=True, padx=5)

        # --- CONSOLE ---
        self.console_output = ctk.CTkTextbox(self, height=180)
        self.console_output.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def browse(self, var):
        folder = filedialog.askdirectory()
        if folder: var.set(folder)

    def run_thread(self, target):
        threading.Thread(target=target, daemon=True).start()

    # --- JSON LOGIC ---
    def load_custom_json(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath: return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            extracted_acronyms = []
            display_list = ""
            for category, features in data.items():
                for name, acronyms in features.items():
                    extracted_acronyms.extend(acronyms)
                    display_list += f"• {name} {acronyms}\n"
                    
            if not extracted_acronyms:
                messagebox.showwarning("Warning", "No S-57 objects found in the selected JSON.")
                return
                
            msg = f"Found {len(extracted_acronyms)} object classes in JSON:\n\n{display_list}\nDo you want to add these to the extraction queue?"
            if messagebox.askyesno("Confirm Custom Features", msg):
                self.custom_targets = list(set(extracted_acronyms))
                self.custom_targets_label_var.set(f"Custom Features Loaded: {len(self.custom_targets)} objects")
                print(f"[+] Successfully loaded {len(self.custom_targets)} custom feature targets.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse JSON file.\n{str(e)}")

    def open_json_builder(self):
        master_json_path = "S57_Object_Classes_Structured.json"
        if not os.path.exists(master_json_path):
            return messagebox.showerror("File Not Found", f"Cannot find '{master_json_path}' in the current directory.")
            
        with open(master_json_path, 'r') as f:
            master_data = json.load(f)
            
        builder_win = ctk.CTkToplevel(self)
        builder_win.title("Custom S-57 Feature Builder")
        builder_win.geometry("650x700")
        builder_win.grab_set() 
        
        ctk.CTkLabel(builder_win, text="Select Object Classes to Export", font=("Arial", 16, "bold")).pack(pady=10)
        
        # --- NEW: Select All / Deselect All Frame ---
        btn_frame = ctk.CTkFrame(builder_win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        tabview = ctk.CTkTabview(builder_win)
        tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        checkbox_dict = {}
        for category, features in master_data.items():
            tabview.add(category)
            scroll = ctk.CTkScrollableFrame(tabview.tab(category))
            scroll.pack(fill="both", expand=True)
            
            checkbox_dict[category] = {}
            for name, acronyms in features.items():
                var = ctk.BooleanVar(value=False)
                checkbox_dict[category][name] = (var, acronyms)
                ctk.CTkCheckBox(scroll, text=f"{name} {acronyms}", variable=var).pack(anchor="w", padx=10, pady=2)
                
        # --- NEW: Checkbox toggle function ---
        def set_all_checkboxes(state):
            for cat_dict in checkbox_dict.values():
                for var, _ in cat_dict.values():
                    var.set(state)
                    
        ctk.CTkButton(btn_frame, text="Select All", width=100, command=lambda: set_all_checkboxes(True)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Deselect All", width=100, command=lambda: set_all_checkboxes(False)).pack(side="left", padx=5)
        
        def save_custom_json():
            output_data = {}
            count = 0
            for cat, features in checkbox_dict.items():
                selected = {name: acro for name, (var, acro) in features.items() if var.get()}
                if selected:
                    output_data[cat] = selected
                    count += len(selected)
                    
            if count == 0: return messagebox.showwarning("Warning", "No features selected.", parent=builder_win)
                
            save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], parent=builder_win)
            if save_path:
                with open(save_path, 'w') as f: json.dump(output_data, f, indent=4)
                messagebox.showinfo("Success", f"Saved {count} custom features to JSON.", parent=builder_win)
                builder_win.destroy()
                
        ctk.CTkButton(builder_win, text="Save Selected to JSON", command=save_custom_json, fg_color="green").pack(pady=10)

    # --- PIPELINE TRIGGERS ---
    def trigger_db_build(self):
        charts_in = self.charts_input.get().strip()
        db_out = self.db_dir.get().strip()
        
        if not charts_in or not db_out: 
            return print("[!] Set Charts and DB paths.")
            
        targets = [l for g, v in self.checkbox_vars.items() if v.get() for l in LAYER_GROUPS[g]]
        targets.extend(self.custom_targets)
        targets = list(set(targets))
        
        # Offload the heavy lifting to the backend engine
        build_database(charts_in, db_out, targets)

    def trigger_ini_build(self):
        db_out = self.db_dir.get().strip()
        ini_out = self.ini_dir.get().strip()
        
        if not db_out or not ini_out: 
            return print("[!] Set DB and INI paths.")
            
        print("\n--- STARTING INI GENERATION ---")
        generate_buoy_ini(db_out, ini_out)
        generate_bcn_ini(db_out, ini_out)
        generate_light_ini(db_out, ini_out)
        print("--- INI GENERATION COMPLETE ---")

if __name__ == "__main__":
    app = SwimMasterGUI()
    app.mainloop()