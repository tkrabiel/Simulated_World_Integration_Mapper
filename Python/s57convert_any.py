import os
import glob
from osgeo import ogr
import json
"""
convert asked for items into a combined JSON file
"""
#find charts in a file strutcture
#return the chart and the str_path
def find_charts_paths(str_path):
    os.chdir(str_path)
    filepaths = []
    for root, dirs, files in os.walk(str_path):
        for file in files:
            if file.endswith(".000"):
                filepaths.append(os.path.join(root,file))
    return filepaths

def charts_from_fp(str_path):
    charts = []
    for x, y in enumerate(find_charts_paths(str_path)):
        return charts.append(find_charts_paths(str_path)[x][-12:-4])

for x,y in enumerate(find_charts("D:/hidden/CHARTS_forbadinternet/ENC_ROOT")):
    print(find_charts("D:/hidden/CHARTS_forbadinternet/ENC_ROOT")[x][-12:-4])

def cvt_obj_json(srt_path,output_path,chart,objects,object_types):
    os.chdir(srt_path)
    #srt_path = "D:/hidden/CHARTS_forbadinternet/ENC_ROOT/US5VA51M" #chart of intrest change child layer
    #output_path = 'D:/hidden/CHARTS_forbadinternet/'
    os.chdir(srt_path)
    #list of buoy OBJECT types
    #objects = ['BOYCAR','BOYINB','BOYISD','BOYLAT','BOYSAW','BOYSPP','DAYMAR']
    #object_types = "Buoys"
    obj_json = {}
    for obj in objects:
        failed = os.system('ogrinfo '+chart+'.000 '+obj)
        if not failed:
            file_name = object_types + obj + '.json'
            write_failed = os.system('ogr2ogr -f "GeoJSON" '+' '+file_name+' '+chart+'.000 '+' '+obj)
            if write_failed:
                raise FileExistsError(f"{file_name} is in use")
            data = json.load(open(file_name))
            obj_json[obj] = data
    data_list = [] #data list of all json files in the path
    #ISSUE!!! IF THERE ARE ANY JSONS ALREADY IN THAT FILE IT WILL ADD ALL OF THEM TOGETHER
    #Maybe Sometimes the user wants that sometimes they dont.
    #Need to give USER A WARNING AND ASK
    # (THE FOLLOWING JSONS WERE FOUND BALABALA IF YOU CONUTIE WILL COMBINE ALL JSONS.
    # DO YOU WANT TO ONLY COMBINE THE NEW JSONS FROM THIS SESSION!!)
    for file in os.listdir(srt_path):#append the file path to the list for each json file
        if object_types in file:
            json_path = os.path.join(file)
            data_list.append(json_path)
            #x = input("I see files do i go on")
            #if x == 'Y':
                #json_path = os.path.join(file)
                #data_list.append(json_path)
            #else:
                #print("Stop")
                #return()


    #update all the JSON files so that they have their source within them i.e BOYLAT, DYMARK ect

    file = data_list[0]
    f1 = json.load(open(os.path.join(file)))

    for name in f1['features']:
        name['properties'].update({"OBJ_SOURCE":f1['name']})
    data_list2 = data_list[1:]
    for name in data_list2:
        f2 = json.load(open(os.path.join(name)))
        for items in f2['features']:
            items['properties'].update({"OBJ_SOURCE": f2['name']})
        f1['features'].extend(f2['features'])

    json.dump(f1, open(os.path.join(output_path+object_types+chart+".json"), 'w'))

    files = glob.glob(output_path + '*.json')
    files_there = []
    for fl in files:
        f = open(fl)
        json_data = json.load(f)
        files_there.append(fl)
    print(files_there)
    for file in files_there:
        data = json.load(open(file))
        obj_json[obj] = data
        for obj_list in obj_json:
            for item in obj_json[obj_list]['features']:
                print(item['properties']["COLOUR"])


def json2ini(export_obj):
    file_dir = 'D:/hidden/CHARTS_forbadinternet/'  # file location
    chart = 'US5VA51M'
    files = glob.glob(file_dir + chart + '*.json')
    files_there = []
    for fl in files:
        f = open(fl)
        json_data = json.load(f)
        files_there.append(fl)
    print(files_there)
    for file in files_there:
        data = json.load(open(file))
        obj_json[obj] = data
        for obj_list in obj_json:
            for item in obj_json[obj_list]['features']:
                print(item['properties'])
    export_obj = 'LIGHTS'
    for item in obj_json[export_obj]['features']:
        x = item['properties']['COLOUR'][0]


        if x == '1':
            print("White")
        elif x == '2':
            print("Black")
        elif x == '3':
            print("Red")
        elif x == '4':
            print('Green')
        else:
            print("OTHER")

            file_dir = 'D:/hidden/CHARTS_forbadinternet/'  # file location

            files = glob.glob(file_dir + '*.json')
            files_there = []
            for fl in files:
                f = open(fl)
                json_data = json.load(f)
                files_there.append(fl)
            print(files_there)
            for file in files_there:
                data = json.load(open(file))
                obj_json[obj] = data
                for obj_list in obj_json:
                    for item in obj_json[obj_list]['features']:
                        print(item['properties']["COLOUR"])



# FOR TESTING USE BELOW

import os
import glob
from osgeo import ogr
import json

srt_path = "D:/hidden/CHARTS_forbadinternet/ENC_ROOT/US5VA25M/"  # chart of intrest change child layer
output_path = 'D:/hidden/CHARTS_forbadinternet/ENC_ROOT/'
chart = "US5VA25M"
# list of buoy OBJECT types
objects = ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP', 'DAYMAR', 'LIGHTS']
object_types = "TEST"
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

json.dump(f1, open(os.path.join(output_path + object_types + chart + ".json"), 'w'))

files = glob.glob(srt_path + '*.json')
files_there = []
for fl in files:
    f = open(fl)
    json_data = json.load(f)
    files_there.append(fl)
print(files_there)
object_1 = 'LIGHTS'
object_2 = 'BOYLAT'
listlight = []
listbuoy = []
for file in files_there:
    data = json.load(open(file))
    obj_json[obj] = data
    print(data)
    for obj_list in obj_json:
        if obj_list == object_1:
            for item in obj_json[object_1]['features']:
                print(item, item['geometry']["coordinates"])
                listlight.append(item['geometry']["coordinates"])
        elif obj_list == object_2:
            for item in obj_json[object_2]['features']:
                listbuoy.append(item['geometry']["coordinates"])
        else:
            print('done')
    for items, x in enumerate(listlight):
        if (x in listbuoy):
            print(listbuoy.index(x))

            f = open("test.ini", "w")
            count = 0
            for items in bj['features']:
                x = str(items['geometry']['coordinates'][0])  # lat
                y = str(items['geometry']['coordinates'][1])  # long
                f.write('Type(%s)="buoy"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (
                str(count), str(count), str(y), str(count), str(x)))
                count += 1
            print(count)
            f.close()
            f = open("test.ini", "r")
            f.read()


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


            f = open("buoy.ini", "w")
            count = 0
            for items in bj['features']:
                x = str(items['geometry']['coordinates'][0])  # lat
                y = str(items['geometry']['coordinates'][1])  # long
                f.write('Type(%s)="port_small"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (
                str(count), str(count), str(y), str(count), str(x)))
                count += 1
            line = "Number={}\n".format(count)
            f.close()
            prepend_line("test.ini", line)