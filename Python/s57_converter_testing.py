# FOR TESTING USE BELOW

import os
import glob
from osgeo import ogr
import json
from S57_attribute_dic import *

def prepend_line(file_name, line):
    """ Insert given string as a new line at the beginning of a file """
    # define name of temporary dummy file
    dummy_file = file_name + '.bak'
    # open original file in read mode and dummy file in write mode
    with open(file_name, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        # Write given line to the dummy file
        write_obj.write(line + '\n')
        # Read lines from original file one by one and append them to the dummy file
        for line in read_obj:
            write_obj.write(line)
    # remove original file
    os.remove(file_name)
    # Rename dummy file as the original file
    os.rename(dummy_file, file_name)

#Buoy Dictionary
#Region: A,B {"shape_color":"buoy_file"}
#Region A
#"1_['3']":"port"  port is a red nun
#Region B
#"1_['3']":"stbd"  stbd is a red nun


#CREATE THE JSON!! 7-54
srt_path = "E:/UMD_Project/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/"  # chart of intrest change child layer
output_path = 'E:/UMD_Project/GIS/Vectors/'
combined_json_outpath = "E:/UMD_Project/GIS/Vectors/combo/"
chart = "US5NYCBG"
ini_output = "E:/UMD_Project/GIS/ini/"
# list of buoy OBJECT types
objects = ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP']
object_types = "Buoy"
os.chdir(srt_path)
obj_json = {}
for obj in objects:
    failed = os.system('ogrinfo ' + chart + '.000 ' + obj)
    if not failed:
        file_name = object_types + obj + '.json'
        write_failed = os.system('ogr2ogr -f "GeoJSON" ' + ' ' + file_name + ' ' + chart + '.000 ' + ' ' + obj)
        if write_failed:
            raise FileExistsError(f"{file_name} is in use")
        data = json.load(open(file_name))
        obj_json[obj] = data
data_list = []  # data list of all json files in the path
# ISSUE!!! IF THERE ARE ANY JSONS ALREADY IN THAT FILE IT WILL ADD ALL OF THEM TOGETHER
# Maybe Sometimes the user wants that sometimes they dont.
# Need to give USER A WARNING AND ASK
# (THE FOLLOWING JSONS WERE FOUND BALABALA IF YOU CONUTIE WILL COMBINE ALL JSONS.
# DO YOU WANT TO ONLY COMBINE THE NEW JSONS FROM THIS SESSION!!)
for file in os.listdir(srt_path):  # append the file path to the list for each json file
    if object_types in file:
        json_path = os.path.join(file)
        data_list.append(json_path)
        # x = input("I see files do i go on")
        # if x == 'Y':
        # json_path = os.path.join(file)
        # data_list.append(json_path)
        # else:
        # print("Stop")
        # return()
# update all the JSON files so that they have their source within them i.e BOYLAT, DYMARK ect
file = data_list[0]
f1 = json.load(open(os.path.join(file)))
for name in f1['features']:
    name['properties'].update({"OBJ_SOURCE": f1['name']})
data_list2 = data_list[1:]
for name in data_list2:
    f2 = json.load(open(os.path.join(name)))
    for items in f2['features']:
        items['properties'].update({"OBJ_SOURCE": f2['name']})
    f1['features'].extend(f2['features'])
chart_json = output_path + object_types + chart + ".json"
json.dump(f1, open(os.path.join(chart_json), 'w'))

#open the json file jsut created
file_json = open(chart_json)
json_data = json.load(file_json)

#combine all the JSON files made into one JSON file

file_list = []
for file in os.listdir(output_path):
    if file.endswith(".json") == True:
        file_list.append(file)
print(file_list)
file_1 = file_list[0]
f1 = json.load(open(os.path.join(output_path+file_1)))
for files in file_list:
    print(files)
    f2 = json.load(open(os.path.join(output_path+files)))
    f1['features'].extend(f2['features'])
final_json = combined_json_outpath+"buoy_all_charts1.json"

json.dump(f1, open(os.path.join(final_json), 'w'))
#open the json file jsut created
file_json = open(final_json)
json_data = json.load(file_json)
#create the INI file below
f = open(ini_output+"buoy.ini", "w")
count = 0
for index, types in enumerate(json_data['features']):
    if "CATCAM" in json_data['features'][index]['properties'] == True:
        key_catcam = str(json_data['features'][index]['properties']["CATCAM"])
        catcam = catcam_dic[key_catcam]
        # boyshp = str(json_data['features'][index]['properties']["BOYSHP"])
        # colour = str(json_data['features'][index]['properties']["COLOUR"])
        key_boyshp = str(json_data['features'][index]['properties']["BOYSHP"])
        key_colour = str(json_data['features'][index]['properties']["COLOUR"])
        boyshp = boyshp_dic[key_boyshp]
        colour = colour_dic[key_colour]
        buoy_type = boyshp + "_" + colour + "_" + catcam
        x = json_data['features'][index]['geometry']['coordinates'][0]
        y = json_data['features'][index]['geometry']['coordinates'][1]
        f.write('Type(%s)="(%s)"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_type),
                                                                  str(count), str(y), str(count), str(x)))
        # f.write('Type(%s)="(%s)"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_to_ini_dic[key_to_lookup]),
        # str(count), str(y), str(count), str(x)))
    else:
        catcam =""
        #boyshp = str(json_data['features'][index]['properties']["BOYSHP"])
        #colour = str(json_data['features'][index]['properties']["COLOUR"])
        key_boyshp = str(json_data['features'][index]['properties']["BOYSHP"])
        key_colour = str(json_data['features'][index]['properties']["COLOUR"])
        boyshp = boyshp_dic[key_boyshp]
        colour = colour_dic[key_colour]
        buoy_type = boyshp+"_"+colour
        x = json_data['features'][index]['geometry']['coordinates'][0]
        y = json_data['features'][index]['geometry']['coordinates'][1]
        f.write('Type(%s)="%s"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_type),
                                                                  str(count), str(y), str(count), str(x)))
        #f.write('Type(%s)="(%s)"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_to_ini_dic[key_to_lookup]),
                                                                  #str(count), str(y), str(count), str(x)))
    count += 1
f.close()
line = "Number={}\n".format(count)
prepend_line(ini_output+"buoy.ini", line)



file_json = open(combined_json_outpath+"buoy_all_charts.json")
json_data = json.load(file_json)
print(json_data)
for num,item in enumerate(json_data):
    print(json_data['features'][num]['properties'])
    for num2,item2 in enumerate(json_data['features'][num]['properties']):
        print(num2)






"""


files = glob.glob(output_path + '*.json')
files_there = []
for fl in files:
    f = open(fl)
    json_data = json.load(f)
    files_there.append(fl)


file = files_there[0]
f1 = json.load(open(os.path.join(file)))
for name in files_there:
    f2 = json.load(open(os.path.join(name)))
    f1['features'].extend(f2['features'])

json.dump(f1, open(os.path.join(output_path + object_types + "allcharts"+ ".json"), 'w'))

for fl in files:
    f = open(fl)
    json_data = json.load(f)
    files_there.append(fl)
print(files_there)
listbuoy = []
for file in files_there:
    data = json.load(open(file))
    obj_json[obj] = data
    print(file,data)
    for obj_types in objects:
        print(obj_types)
        for obj_list in obj_json:
            print(obj_list)
            if obj_list == obj_types:
                for item in obj_json[obj_types]['features']:
                    print(item['geometry']["coordinates"])
                    listbuoy.append(item['geometry']["coordinates"])
            else:
                print('done')

for pos, item in enumerate(listbuoy):
    if (item in listbuoy):
        # print(listbuoy.index(x))
        print(item)
        f = open("buoy.ini", "w")
        count = 0
        for item in obj_json['BOYLAT']['features']:
            x = str(item['geometry']['coordinates'][0])  # lat
            print(x)
            y = str(item['geometry']['coordinates'][1])  # long
            f.write('Type(%s)="port"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (
                str(count), str(count), str(y), str(count), str(x)))
            count += 1
        f.close()
        f = open("buoy.ini", "r")
        f.read()
        f.close()
        line = "Number={}\n".format(count)
        prepend_line("buoy.ini", line)
        
        
        
#COLORS FOR LIGHTS
import matplotlib
ex for Violet
red = matplotlib.colors.to_rgb(colour_dic["['10']"])[0]*255
green = matplotlib.colors.to_rgb(colour_dic["['10']"])[1]*255
blue = matplotlib.colors.to_rgb(colour_dic["['10']"])[2]*255
"""