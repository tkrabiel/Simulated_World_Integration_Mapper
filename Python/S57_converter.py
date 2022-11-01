import os
import glob
from osgeo import ogr
import json
from S57_attribute_dic import *
import re
import matplotlib
import math

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

def S57_to_json(str_path,output_path,chart,objects,object_types):
    #str_path = "E:/UMD_Project/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/"  # chart of intrest change child layer
    #output_path = 'E:/UMD_Project/GIS/Vectors/'
    #chart = "US5NYCBG"
    #objects = ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP']
    #object_types = "Buoy"
    os.chdir(str_path)
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
    for file in os.listdir(str_path):  # append the file path to the list for each json file
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

def combo_json(output_path,combined_json_outpath,object_types):
    # combine all the JSON files made into one JSON file
    file_list = []
    for file in os.listdir(output_path):
        if file.endswith(".json") == True:
            file_list.append(file)
    print(file_list)
    file_1 = file_list[0]
    f1 = json.load(open(os.path.join(output_path + file_1)))
    for files in file_list:
        print(files)
        f2 = json.load(open(os.path.join(output_path + files)))
        f1['features'].extend(f2['features'])
    final_json = combined_json_outpath+object_types+"_combined.json"
    json.dump(f1, open(os.path.join(final_json), 'w'))
    return final_json
def json_to_ini_buoy(ini_output,json_file_path):
    file_json = open(json_file_path)
    json_data = json.load(file_json)
    # create the INI file below
    ini_file = open(ini_output + "buoy.ini", "w")
    count = 0
    for index, types in enumerate(json_data['features']):
        if "CATCAM" in json_data['features'][index]['properties'] == True:
            key_catcam = str(json_data['features'][index]['properties']["CATCAM"])
            catcam = catcam_dic[key_catcam]
            #boyshp = str(json_data['features'][index]['properties']["BOYSHP"])
            # colour = str(json_data['features'][index]['properties']["COLOUR"])
            key_boyshp = str(json_data['features'][index]['properties']["BOYSHP"])
            #key_colour = str(json_data['features'][index]['properties']["COLOUR"])
            boyshp = boyshp_dic[key_boyshp]
            #colour = colour_dic[key_colour]
            buoy_type = boyshp+"_"+catcam
            x = json_data['features'][index]['geometry']['coordinates'][0]
            y = json_data['features'][index]['geometry']['coordinates'][1]
            ini_file.write('Type(%s)="%s"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_type),
                                                                      str(count), str(y), str(count), str(x)))
            # f.write('Type(%s)="(%s)"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_to_ini_dic[key_to_lookup]),
            # str(count), str(y), str(count), str(x)))
        else:
            # boyshp = str(json_data['features'][index]['properties']["BOYSHP"])
            # colour = str(json_data['features'][index]['properties']["COLOUR"])
            key_boyshp = str(json_data['features'][index]['properties']["BOYSHP"])
            key_colour = str(json_data['features'][index]['properties']["COLOUR"])
            boyshp = boyshp_dic[key_boyshp]
            colour = colour_dic[key_colour]
            buoy_type = boyshp + "_" + colour
            x = json_data['features'][index]['geometry']['coordinates'][0]
            y = json_data['features'][index]['geometry']['coordinates'][1]
            ini_file.write('Type(%s)="%s"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_type),
                                                                    str(count), str(y), str(count), str(x)))
            # f.write('Type(%s)="(%s)"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_to_ini_dic[key_to_lookup]),
            # str(count), str(y), str(count), str(x)))
        count += 1
    ini_file.close()
    line = "Number={}\n".format(count)
    prepend_line(ini_output + "buoy.ini", line)

#LIGHT CONVERTION



#convert the light charactersitics into the ini needed foramat of DL
#D or L = 0.25 seconds
def light(time):
    light_on_list = []
    while time>0:
        light_on_list.append("L")
        time -= 0.25
    out = "".join(light_on_list)
    return out


def dark(time):
    light_off_list = []
    while time>0:
        light_off_list.append("D")
        time -= 0.25
    out = "".join(light_off_list)
    return out


def light_seq(light_time_list):
    temp = re.findall(r'\d+\.\d+', light_time_list)
    res = list(map(float, temp))
    if light_time_list[0] == '(':
        seq = 'DL'
    else:
        seq = 'LD'
    count = len(res)
    flash = []
    if len(res) == 1:
        if seq == 'DL':
            flash.append(dark(res[count-1]))
        else:
            flash.append(light(res[count-1]))
    elif (len(res) % 2) == 0:
        if seq == 'DL':
            while count > 0:
                flash.insert(0,light(res[count - 1]))
                flash.insert(0,dark(res[count - 2]))
                count -= 2
        elif seq == 'LD':
            while count > 0:
                flash.insert(0,dark(res[count-1]))
                flash.insert(0,light(res[count-2]))
                count -= 2
    else:
        if seq == 'LD':
            while count > 1:
                flash.insert(0, light(res[count - 1]))
                flash.insert(0, dark(res[count - 2]))
                count -= 2
                print(count)
            print(count)
            flash.insert(0, light(res[count - 1]))
            count -= 1
        elif seq == 'DL':
            while count > 1:
                flash.insert(0, dark(res[count - 1]))
                flash.insert(0, light(res[count - 2]))
                count -= 2
            flash.insert(0, dark(res[count-1]))
            count -= 1
    light_char = ''.join(flash)
    return(light_char)


def json_to_ini_light(ini_output,json_file_path,height_eye):
    if "Lights_" in json_file_path:
        file_json = open(json_file_path)
        json_data = json.load(file_json)
        # create the INI file below
        ini_file = open(ini_output + "light.ini", "w")
        count = 0
        for index, types in enumerate(json_data['features']):
            key_colour = str(json_data['features'][index]['properties']["COLOUR"])
            colour = colour_dic[key_colour]
            try:
                key_SIGSEQ = str(json_data['features'][index]['properties']["SIGSEQ"])
                sequence = light_seq(key_SIGSEQ)
            except KeyError:
                sequence = 'L'
            try:
                key_SECTR1 = str(json_data['features'][index]['properties']["SECTR1"])
                key_SECTR2 = str(json_data['features'][index]['properties']["SECTR2"])
                StartAngle = str(key_SECTR1)[:-2]
                EndAngle = str(key_SECTR2)[:-2]
            except KeyError:
                StartAngle = '0'
                EndAngle = '360'
            try:
                key_height = str(json_data['features'][index]['properties']["HEIGHT"])
                height = str(key_height)[:-2]
            except KeyError:
                height = '3.5'
            range_light = int(1.17 * (math.sqrt((float(height)*3.3) + math.sqrt(float(height_eye)*3.3))))
            range = int(round(range_light))
            red = int(matplotlib.colors.to_rgb(colour)[0] * 255)
            green = int(matplotlib.colors.to_rgb(colour)[1] * 255)
            blue = int(matplotlib.colors.to_rgb(colour)[2] * 255)
            x = json_data['features'][index]['geometry']['coordinates'][0]
            y = json_data['features'][index]['geometry']['coordinates'][1]
            ini_file.write('Lat(%s)=%s\nLong(%s)=%s\nHeight(%s)=%s\nRed(%s)=%s\nGreen(%s)=%s\nBlue(%s)=%s\nRange(%s)=%s'
                           '\nSequence(%s)="%s"\nStartAngle(%s)=%s\nEndAngle(%s)=%s\n\n'
                           % (str(count+1), str(y), str(count+1), str(x),str(count+1),
                              str(height),str(count+1), str(red),str(count+1), str(green),str(count+1),
                              str(blue),str(count+1), str(range),str(count+1), str(sequence),str(count+1),
                              str(StartAngle),str(count+1), str(EndAngle)))
        # f.write('Type(%s)="(%s)"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (str(count), str(buoy_to_ini_dic[key_to_lookup]),
        # str(count), str(y), str(count), str(x)))
            count += 1
        ini_file.close()
        line = "Number={}\n".format(count)
        prepend_line(ini_output + "light.ini", line)
    else:
        return(None)

json_file_path = gpd.read_file("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBF/ENC_ROOT/US5NYCBF/soundSOUNDG.json/")



def multitosingle(json_file_path):
    df = gpd.read_file(json_file_path)
    #json_data = json.load(file_json)
    for idx, row in df.iterrows():
        for shp in row.geometry:
            x.append(shp.z)

"""
#SOUNGIND TEST
import geopandas as gpd
df = gpd.read_file(r"E:\UMD_Project\SWIM\GIS\Charts\US5NYCBF\ENC_ROOT\US5NYCBF\US5VA51M.shp")
for idx, row in df.iterrows():
    for shp in row.geometry:
        print(shp.x,shp.y,shp.z)





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