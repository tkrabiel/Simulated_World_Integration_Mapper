# SWIM (Simulated World Integration Mapper)

> PROJECT STATUS: Active Development & In Progress
> I am actively developing, iterating, and expanding this project. I am continuously fixing pipeline bugs, refining the architecture for better readability, and finding ways to further optimize the system.

SWIM is my custom, highly optimized spatial pipeline designed to scrape NOAA S-57 electronic navigational charts (.000 files), extract and compress vector spatial data into a high-performance GeoParquet database, and instantly generate world configuration files (.ini) and Digital Elevation Models (DEMs) for the Bridge Command ship simulator.

---

## Key Features

* Modular Custom Feature Scraping: I built a dynamic JSON loading system. Using the official IHO S-57 Object Class catalog, users can build, save, and load custom .json files to scrape *any* specific feature from the charts (e.g., Wrecks, Obstructions, Piers, Coastlines, Unsurveyed Areas) beyond the standard navigation aids.
* Smart Delta-Updates (Soft Deletes): I implemented an advanced upsert logic. When rescanning specific charts, the database compares old geometries against the new data. If a feature was removed by NOAA in the updated charts, it is flagged as REMOVED in the database. This preserves historical records while ensuring the simulator only loads active, real-world data.
* Intelligent Spatial Deduplication: My pipeline automatically detects overlapping chart boundaries and merges identical features based on precise physical geometry (WKT) to prevent duplicate assets from spawning in the simulator.
* Single-File GeoParquet Architecture: I designed the backend to consolidate massive batches of complex S-57 charts into a clean, single-file-per-layer format (e.g., one master LIGHTS.parquet file for your entire target area), preserving overlapping chart metadata as nested arrays.
* Advanced Attribute Parsing: I integrated official Teledyne CARIS fallback logic. The pipeline dynamically reads COLPAT (Color Patterns) to append specific tags like _horizontal_stripes or _diagonal_stripes to buoys and beacons. It also forcefully corrects missing data (e.g., defaulting textureless beacons to magenta_solid).
* Instant INI Generation: I utilize high-efficiency row-streaming (itertuples) to generate Bridge Command buoy.ini, bcn.ini, and light.ini files in milliseconds without encountering memory bottlenecks.

---

## Installation & Prerequisites

1. Python: Ensure you have Python 3.9 or newer installed.
2. Install Dependencies: Run the following command in your terminal to install the libraries I am using:
   
   pip install -r requirements.txt

Core Libraries I Depend On:
* customtkinter (Modern GUI Framework)
* geopandas, pandas, pyarrow (Spatial Data Processing & High-Performance Parquet Engine)
* rasterio, pystac-client, planetary-computer, s3fs (Cloud-Optimized Raster Engines)

---

## Usage Guide

Launch my main interface by executing:
python main_gui.py

### Step 1: Scrape & Build the Database
1. Charts Link/Folder: Provide a local directory path containing your unzipped .000 NOAA charts, OR paste a direct URL to a .zip file containing charts (my tool will download and extract it automatically).
2. Database (GeoParquet): Select or create an empty directory where I will save your compiled database layers.
3. Select Features: Toggle the standard S-57 layers you wish to extract (Lights, Buoys, Beacons, Land, Dredge, etc.). 
4. (Optional) Custom JSON: Click "Build Custom JSON" to select advanced object classes (like Wrecks or Bridges) from the master dictionary, save your selection, and load it into the extraction queue.
5. Click "1. Build Database". My backend engine will extract, deduplicate, process removals, and compress the charts.

### Step 2: Generate Bridge Command INIs
1. Output INI Folder: Select your destination directory for the simulation assets.
2. Click "2. Generate Bridge Command INIs". My tool instantly queries the Parquet layers, filters out any REMOVED features, calculates exact light ranges, translates S-57 color/pattern codes, and outputs buoy.ini, bcn.ini, and light.ini.

---

## Active Engineering & In-Progress Improvements

I am actively refining the platform with a heavy focus on better code readability, deeper attribute parsing, and custom terrain blending:

* Separation of Concerns: I recently separated the core database compilation logic from the CustomTkinter UI. I am continuing to refactor legacy logic, standardize variable typings, and optimize error handlers across all modules to make the codebase highly maintainable and API-ready.
* Advanced TopoBathy DEM Generation: I am currently working to stabilize the pipeline so it seamlessly blends cloud-streamed Topography (USGS 3DEP) and Bathymetry (NOAA BlueTopo) datasets. By leveraging S-57 LNDARE (Land Area) and DRGARE (Dredge Area) vector polygons, my goal is to automatically burn accurate elevation masks into the underlying terrain arrays.

---

## Future Roadmap: Building Virtual Realms

My long-term vision for SWIM is to evolve it from a local asset parser into a completely automated, web-integrated world-building engine:

1. Standalone Executable File (.exe): I plan to compile my CustomTkinter GUI using PyInstaller into a unified, zero-dependency Windows executable file so users can build worlds without needing a local Python environment.
2. Online Feature Databases: I intend to transition away from flat file storage toward a remote, cloud-hosted geospatial database (e.g., PostGIS) capable of handling massive continent-scale feature datasets.
3. Dynamic API Integration: I will build a headless web API that allows my application to directly stream features from cloud databases on-the-fly based on a user's chosen coordinate bounding box.
4. On-Demand Virtual Realms: My ultimate goal is to let users point to *any* coastal coordinate boundary on Earth, ping the NOAA charts and cloud DEM databases via my future API, and instantly spin up a completely synthesized, geographically precise virtual realm ready for simulator deployment.

---

## Module Breakdown

| File | Description |
| :--- | :--- |
| main_gui.py | My main UI app. Handles routing, file paths, the Custom JSON Feature Builder interface, and triggers the backend processing threads. |
| s57_database_builder.py | My dedicated backend engine. Handles chart downloading, multi-chart data scraping, WKT spatial deduplication, database delta-updates (soft deletes), and master GeoParquet compression. |
| s57_vector_pipeline.py | My high-efficiency asset generator. Streams Parquet layers via fast tuples, applies Teledyne CARIS color/pattern fallback rules, and writes simulator files in milliseconds. |
| s57_raster_pipeline.py | (I am still fixing this) Merges topography and bathymetry data using S-57 shape masks to export accurate terrain.ini profiles. |
| cloud_dem_pipeline.py | (I am still fixing this) Automatically pulls chart boundaries (M_COVR), queries cloud STAC catalogs, and streams clipped DEM rasters into memory. |
| s57_dictionaries.py | My lookup engine. Maps raw S-57 codes and COLPAT variables to simulator definitions, with built-in protection against NumPy truth-value crashes and float artifacts. |
