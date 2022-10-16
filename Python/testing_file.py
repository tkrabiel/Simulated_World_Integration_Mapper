# importing the library
import os
import S57_converter as sc

# giving directory name
folderdir = 'E:/UMD_Project/SWIM/GIS/Charts/'
# giving file extension
ext = ('.000')

output_path = "E:/UMD_Project/SWIM/GIS/Charts/"
objects = ['LIGHTS']
object_types = "Lights"
ini_output = "E:/UMD_Project/SWIM/GIS/Charts/"
combined_json_outpath = "E:/UMD_Project/SWIM/GIS/Charts/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path, chart, objects, object_types)
json_file_path = sc.combo_json(output_path,combined_json_outpath,object_types)
sc.json_to_ini_light(ini_output,json_file_path,10)

objects = ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP']
object_types = "Buoy"
ini_output = "E:/UMD_Project/SWIM/GIS/Charts/"
combined_json_outpath = "E:/UMD_Project/SWIM/GIS/Charts/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path, chart, objects, object_types)
json_file_path = sc.combo_json(output_path,combined_json_outpath,object_types)
sc.json_to_ini_buoy(ini_output,json_file_path)


