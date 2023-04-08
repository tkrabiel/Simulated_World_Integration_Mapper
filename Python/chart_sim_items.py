# importing the library
import os
import S57_converter as sc
from PIL import Image
import rasterio
from pyproj import Geod
from osgeo import gdal, gdal_array
import rasterio
import numpy


# giving directory name
#folderdir = 'E:/UMD_Project/SWIM/GIS/Charts/'
folderdir = 'E:/UMD_Project/SWIM/GIS/Charts/'

# giving file extension
ext = ('.000')
height_eye = 21 #set height of the users eye in Meters
#topobathy_dem = r"E:\UMD_Project\SWIM\GIS\Rasters\TopoBathy_DEM\small_test.tif"
#xyz_file = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz"
#xyz_csv = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz"
xyz_file = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz"
xyz_csv = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz"
# output = r"E:\UMD_Project\SWIM\GIS\Rasters\TopoBathy_DEM"



output_path_light = folderdir+"json/lights/temp/"
objects_light = ['LIGHTS']
object_types_light = "Lights"
#ini_output = "E:/UMD_Project/SWIM/GIS/ini/"
ini_output = folderdir +"ini/"
combined_json_outpath_light = folderdir +"json/lights/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path

            sc.S57_to_json(str_path, output_path_light, chart, objects_light, object_types_light)
json_file_path = sc.combo_json(output_path_light,combined_json_outpath_light,object_types_light)
try:
    sc.json_to_ini_light(ini_output, json_file_path, height_eye)
except NameError:
    sc.json_to_ini_light(ini_output, json_file_path, 15) #standerd height of eye set at 15 meters




output_path_buoy = folderdir +"json/buoy/temp/"
objects_buoy = ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP']
object_types_buoy = "Buoy"
ini_output = folderdir +"ini/"
combined_json_outpath_buoy = folderdir +"buoy/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path_buoy, chart, objects_buoy, object_types_buoy)
json_file_path_buoy = sc.combo_json(output_path_buoy,combined_json_outpath_buoy,object_types_buoy)
sc.json_to_ini_buoy(ini_output,json_file_path_buoy)


output_path_bcn = folderdir +"json/bcn/temp/"
objects_bcn = ['BCNLAT','BCNCAR','BCNISD','BCNSAW','BCNSPP']
object_types_bcn = "BCN"
ini_output = folderdir +"ini/"
combined_json_outpath_bcn = folderdir +"bcn/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path_bcn, chart, objects_bcn, object_types_bcn)
json_file_path_bcn = sc.combo_json(output_path_bcn,combined_json_outpath_bcn,object_types_bcn)
sc.json_to_ini_bcn(ini_output,json_file_path_bcn)

# output_path_d = folderdir + "json/dredge/temp/"
# objects_d = ['DRGARE']
# object_types_d = "dredge"
# combined_json_outpath_d = folderdir + "json/dredge/"
# # iterating over directory and subdirectory to get desired result
# for path, dirc, files in os.walk(folderdir):
#     for name in files:
#         if name.endswith(ext):
#             chart = name[:-4]
#             str_path = path
#             sc.S57_to_json(str_path, output_path_d, chart, objects_d, object_types_d)
# json_file_path_d = sc.combo_json(output_path_d,combined_json_outpath_d,object_types_d)
#
#
# output_path_land = folderdir + "json/land/temp/"
# objects_land = ['LNDARE']
# object_types_land = "land"
# combined_json_outpath_land = folderdir + "json/land/"
# # iterating over directory and subdirectory to get desired result
# for path, dirc, files in os.walk(folderdir):
#     for name in files:
#         if name.endswith(ext):
#             chart = name[:-4]
#             str_path = path
#             sc.S57_to_json(str_path, output_path_land, chart, objects_land, object_types_land)
# json_file_path_land = sc.combo_json(output_path_land,combined_json_outpath_land,object_types_land)
#
# output_path_extent = folderdir + "json/extent/temp/"
# objects_extent = ['M_COVR']
# object_types_extent = "extent"
# combined_json_outpath_land = folderdir + "json/extent/"
# # iterating over directory and subdirectory to get desired result
# for path, dirc, files in os.walk(folderdir):
#     for name in files:
#         if name.endswith(ext):
#             chart = name[:-4]
#             str_path = path
#             sc.S57_to_json(str_path, output_path_extent, chart, objects_extent, object_types_extent)
# json_file_path_land = sc.combo_json(output_path_extent,combined_json_outpath_land,object_types_extent)
#
#
# output_path_sound = folderdir + "json/sound/temp/"
# objects_sound = ['SOUNDG']
# object_types_sound = "sound"
# ini_output = folderdir + "ini/"
# combined_json_outpath_sound = folderdir + "json/sound/"
# #output_path_sound = "E:/UMD_Project/SWIM/GIS/json/sound"
# # iterating over directory and subdirectory to get desired result
#
# for path, dirc, files in os.walk(folderdir):
#     for name in files:
#         if name.endswith(ext):
#             chart = name[:-4]
#             str_path = path
#             sc.S57_to_json(str_path, output_path_sound, chart, objects_sound, object_types_sound)
# json_file_path = sc.combo_json(output_path_sound,combined_json_outpath_sound,object_types_sound)
# #print(json_file_path)
# json = "sound_combined.json"
# shp = combined_json_outpath_sound+"/sound.shp"
# sc.json_shp(json_file_path,shp)
#
# DRGARE_json = combined_json_outpath_d+object_types_d+"_combined.json"
# LANDAREA_json = combined_json_outpath_land+object_types_land+"_combined.json"
#
# print("DredgeJSON: "+ json_file_path_d)
# #"E:\UMD_Project\SWIM\GIS\json\dredge\dredge_combined.json"
# sc.S57_raster(shp, output_path_sound, xyz_file+"/")