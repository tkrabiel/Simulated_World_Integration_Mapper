# importing the library
import os
import S57_converter as sc

# giving directory name
folderdir = 'E:/UMD_Project/SWIM/GIS/Charts/'
# giving file extension
ext = ('.000')
#height_eye = 21 #standerd height of eye set at 15 meters

output_path = "E:/UMD_Project/SWIM/GIS/json/lights/temp/"
objects = ['LIGHTS']
object_types = "Lights"
ini_output = "E:/UMD_Project/SWIM/GIS/ini/"
combined_json_outpath = "E:/UMD_Project/SWIM/GIS/json/lights/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path, chart, objects, object_types)
json_file_path = sc.combo_json(output_path,combined_json_outpath,object_types)
try:
    sc.json_to_ini_light(ini_output, json_file_path, height_eye)
except NameError:
    sc.json_to_ini_light(ini_output, json_file_path, 15) #standerd height of eye set at 15 meters





output_path = "E:/UMD_Project/SWIM/GIS/json/buoy/temp/"
objects = ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP']
object_types = "Buoy"
ini_output = "E:/UMD_Project/SWIM/GIS/ini/"
combined_json_outpath = "E:/UMD_Project/SWIM/GIS/json/buoy/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path, chart, objects, object_types)
json_file_path = sc.combo_json(output_path,combined_json_outpath,object_types)
sc.json_to_ini_buoy(ini_output,json_file_path)

output_path = "E:/UMD_Project/SWIM/GIS/json/buoy/temp/"
objects = ['SOUNDG']
object_types = "sound"
ini_output = "E:/UMD_Project/SWIM/GIS/ini/"
combined_json_outpath = "E:/UMD_Project/SWIM/GIS/json/buoy/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path, chart, objects, object_types)
json_file_path = sc.combo_json(output_path,combined_json_outpath,object_types)
sc.json_to_ini_buoy(ini_output,json_file_path)


