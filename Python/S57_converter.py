import os
import glob
import osgeo
import osgeo.ogr
import pandas as pd
from osgeo import ogr
import json
from S57_attribute_dic import *
import re
import matplotlib
import math
#import geopandas as gpd
from osgeo import gdal, gdal_array
import geopandas as gpd
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import MultiPoint
import os
import numpy as np

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
    # update all the JSON files so that they have their source within them i.e BOYLAT, DYMARK, DREDGE ect
    try:
        file = data_list[0]
        print(file)
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
    except IndexError:
        print(obj+" Not in this chart")



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

def json_shp(json,shp):
    os.system('ogr2ogr -f "ESRI Shapefile" ' + ' ' + shp + ' ' + json)

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

# json_file_path = gpd.read_file("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBF/ENC_ROOT/US5NYCBF/soundSOUNDG.json")
#
#
#
# def multitosingle(json_file_path):
#     df = gpd.read_file(json_file_path)
#     json_data = json.load(file_json)
#     for idx, row in df.iterrows():
#         for shp in row.geometry:
#             x.append(shp.z)

# from osgeo import gdal
# import geopandas as gpd
# import geopandas as gpd
# from shapely.geometry import Point
# from shapely.geometry import MultiPoint
# import os
# SOUNDG_file = r"E:\UMD_Project\SWIM\GIS\Charts\US5NYCBG\ENC_ROOT\US5NYCBG\SOUNDG.shp"
# DRGARE_json = "E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/dredgeDRGARE.json"
# input_folder = "E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/"
# output_folder = "E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/"
#
#
# def S57_raster(SOUNDG_file, input_folder, output_folder, DRGARE_json):
#     df = gpd.read_file(SOUNDG_file)
#     xyzcsv = input_folder + "/xyz.csv"
#     xyzvrt = input_folder + "/xyz.vrt"
#     with open(xyzcsv, "w") as f:
#         f.write('x,y,z\n')
#     for idx, row in df.iterrows():
#         for shp in row.geometry:
#             with open(xyzcsv, "a") as f:
#                 f.write(str(shp.x) + ',' + str(shp.y) + ',' + str(shp.z) + '\n')
#     try:
#
#     polys = gpd.read_file(DRGARE_json)
#     # copy GeoDataFrame
#     # points2 = polys.copy()
#     # points2.geometry = points2.geometry.apply(lambda x: MultiPoint(list(x.exterior.coords)))
#     # new GeoDataFrame with same columns
#     # Extraction of the polygon nodes and attributes values from polys and integration into the new GeoDataFrame
#     for index, row in polys.iterrows():
#         for j in list(row['geometry'].exterior.coords):
#             with open(xyzcsv, "a") as f:
#                 f.write(str(j[0]) + ',' + str(j[1]) + ',' + str(row['DRVAL1']) + '\n')
#     with open(xyzvrt, "w") as f:
#         f.write('''<OGRVRTDataSource>
#         <OGRVRTLayer name="xyz">
#             <SrcDataSource relativeToVRT="1">xyz.csv</SrcDataSource>
#             <LayerSRS>WGS84</LayerSRS>
#             <GeometryType>wkbPoint</GeometryType>
#             <GeometryField encoding="PointFromColumns" x="x" y="y" z="z"/>
#         </OGRVRTLayer>
#     </OGRVRTDataSource>''')
#
#     nn = gdal.Grid(output_folder + "/123invdistnn_xyz.tif", xyzvrt, zfield='z', algorithm="invdistnn")
#     nn = None

def point_in_polygon(polygon):
    minx, miny,maxx,maxy = polygon.bounds
    x = np.random.uniform(minx,maxx,115)
    y = np.random.uniform(miny,maxy,115)
    return x,y
def S57_shape_raster(str_path,json_file_name,tif,output_file_path,output_tif,object,z_value):
    os.chdir(str_path)
    polys = gpd.read_file(str_path+"/"+json_file_name+'.json')
    buffer = polys.copy()
        # copy GeoDataFrame
        # points2 = polys.copy()
        # points2.geometry = points2.geometry.apply(lambda x: MultiPoint(list(x.exterior.coords)))
        # new GeoDataFrame with same columns
        # Extraction of the polygon nodes and attributes values from polys and integration into the new GeoDataFrame
    buffer.geometry = buffer.geometry.apply(lambda x: x.buffer(0.000001))
    buffer.to_file(object, driver='ESRI Shapefile', schema=None)
    #os.system('ogr2ogr -f "ESRI Shapefile" '+object+'.shp '+ json_file_name+'.json')
    fn_ras = tif
    fn_vec = str_path+'/'+object+'/'+object+'.shp'
    ras_ds = gdal.Open(fn_ras)
    vec_ds = osgeo.ogr.Open(fn_vec)
    lyr = vec_ds.GetLayer()
    geot = ras_ds.GetGeoTransform()
    out_net = output_file_path+'/'+output_tif
    drv_tiff = gdal.GetDriverByName("GTiff")
    chn_ras_ds = drv_tiff.Create(out_net, ras_ds.RasterXSize, ras_ds.RasterYSize, 1, gdal.GDT_Float32)
    chn_ras_ds.SetGeoTransform(geot)
    gdal.RasterizeLayer(chn_ras_ds, [1], lyr, options=['ATTRIBUTE='+z_value])
    chn_ras_ds.GetRasterBand(1).SetNoDataValue(0.0)
    chn_ras_ds = None


def raster_mask(output_file_path,output_tif):
    input_tiff = output_file_path+'/'+output_tif
    output_tiff = output_file_path+'/'+'mask_'+output_tif
    ds = gdal.Open(input_tiff)
    b1 = ds.GetRasterBand(1)
    arr = b1.ReadAsArray()
    data = np.where(arr > 1, 0, 1)
    gdal_array.SaveArray(data.astype("float32"), output_tiff, "GTIFF", ds)
    ds = None

def raster_inverse_mask(output_file_path, output_tif):
    input_tiff = output_file_path + '/' + output_tif
    output_tiff = output_file_path + '/' + 'mask_inverse_' + output_tif
    ds = gdal.Open(input_tiff)
    b1 = ds.GetRasterBand(1)
    arr = b1.ReadAsArray()
    data = np.where(arr < 0, 0, 1)
    gdal_array.SaveArray(data.astype("float32"), output_tiff, "GTIFF", ds)
    ds = None
def bathydem_dredge(bathy_dem_path, output_file_path,output_file_path_mask, dredge_raster_path, dredge_raster_name):
    bathy_dem = bathy_dem_path
    dredge_raster = dredge_raster_path
    bathy_dem_dredge = output_file_path + '/' + 'bathy_dem.tif'
    raster_mask(output_file_path_mask, dredge_raster_name)
    bathy_dem_ds = gdal.Open(bathy_dem)
    dredge_raster_ds = gdal.Open(dredge_raster)
    dredge_raster_mask_ds = gdal.Open(output_file_path_mask + '/' + 'mask_' + dredge_raster_name)
    b1 = bathy_dem_ds.GetRasterBand(1)
    b2 = dredge_raster_ds.GetRasterBand(1)
    b3 = dredge_raster_mask_ds.GetRasterBand(1)
    arr1 = b1.ReadAsArray()
    arr2 = b2.ReadAsArray()
    arr3 = b3.ReadAsArray()
    data = (arr1*arr3)+(-1*arr2)
    gdal_array.SaveArray(data.astype("float32"), bathy_dem_dredge, "GTIFF", bathy_dem_ds)
    print('bathy_dem_with_dredge done!!')


def S57_raster(SOUNDG_file, input_folder, output_folder):
    df = gpd.read_file(SOUNDG_file)
    xyzcsv = input_folder + "/xyz.csv"
    xyzvrt = input_folder + "/xyz.vrt"
    with open(xyzcsv, "w") as f:
        f.write('x,y,z\n')
    for idx, row in df.iterrows():
        for shp in row.geometry:
            with open(xyzcsv, "a") as f:
                f.write(str(shp.x) + ',' + str(shp.y) + ',' + str(shp.z*-1) + '\n')
    # exists_land = os.path.isfile(LANDAREA_json)
    # if exists_land:
    #     polys = gpd.read_file(LANDAREA_json)
    #     # copy GeoDataFrame
    #     # points2 = polys.copy()
    #     # points2.geometry = points2.geometry.apply(lambda x: MultiPoint(list(x.exterior.coords)))
    #     # new GeoDataFrame with same columns
    #     # Extraction of the polygon nodes and attributes values from polys and integration into the new GeoDataFrame
    #     polys["buffered"] = polys.buffer(0.0000001)
    #     poly_1 = polys.set_geometry("buffered")
    #     for index, row in poly_1.iterrows():
    #         for j in list(row['buffered'].exterior.coords):
    #             with open(xyzcsv, "a") as f:
    #                 f.write(str(j[0]) + ',' + str(j[1]) + ',' + str(1) + '\n')
    # else:
    #     print("no land area file")
    # exists_land = os.path.isfile(LANDAREA_json)
    # if exists_land:
    #     polys = gpd.read_file(LANDAREA_json)
    #     # copy GeoDataFrame
    #     # points2 = polys.copy()
    #     # points2.geometry = points2.geometry.apply(lambda x: MultiPoint(list(x.exterior.coords)))
    #     # new GeoDataFrame with same columns
    #     # Extraction of the polygon nodes and attributes values from polys and integration into the new GeoDataFrame
    #     polys["buffered"] = polys.buffer(0.0000001)
    #     poly_1 = polys.set_geometry("buffered")
    #     for index, row in poly_1.iterrows():
    #         for j in list(row['buffered'].exterior.coords):
    #             with open(xyzcsv, "a") as f:
    #                 f.write(str(j[0]) + ',' + str(j[1]) + ',' + str(1) + '\n')
    # else:
    #     print("no land area file")
    with open(xyzvrt, "w") as f:
        f.write('''<OGRVRTDataSource>
        <OGRVRTLayer name="xyz">
            <SrcDataSource relativeToVRT="1">xyz.csv</SrcDataSource>
            <LayerSRS>WGS84</LayerSRS>
            <GeometryType>wkbPoint</GeometryType>
            <GeometryField encoding="PointFromColumns" x="x" y="y" z="z"/>
        </OGRVRTLayer>
    </OGRVRTDataSource>''')
    nn = gdal.Grid(output_folder + "/xyz.tif", xyzvrt, zfield='z', algorithm="invdistnn")
    nn = None

# import rasterio
# dataset = rasterio.open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/123invdistnn_xyz.tif")
# dataset.bounds
# from pyproj import Geod
# g = Geod(ellps='WGS84')
# # 2D distance in meters with longitude, latitude of the points
# azimuth1, azimuth2, distance_2d = g.inv(dataset.bounds[0],dataset.bounds[1], dataset.bounds[2],dataset.bounds[1])
# print(distance_2d*0.000001186)
# from pyproj import Geod
# g = Geod(ellps='WGS84')
# # 2D distance in meters with longitude, latitude of the points
# azimuth1, azimuth2, distance_2d = g.inv(dataset.bounds[0],dataset.bounds[1], dataset.bounds[2],dataset.bounds[1])
# print(distance_2d*0.00000118)


# df = gpd.read_file(r"E:\UMD_Project\SWIM\GIS\Charts\US5NYCBG\ENC_ROOT\US5NYCBG\SOUNDG.shp")
# with open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.csv", "w") as f:
#     f.write('x,y,z\n')
# for idx, row in df.iterrows():
#     for shp in row.geometry:
#         with open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.csv", "a") as f:
#             f.write(str(shp.x)+','+str(shp.y)+','+str(shp.z)+'\n')
# polys = gpd.read_file("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/dredgeDRGARE.json")
# # copy GeoDataFrame
# #points2 = polys.copy()
# #points2.geometry = points2.geometry.apply(lambda x: MultiPoint(list(x.exterior.coords)))
# # new GeoDataFrame with same columns
# # Extraction of the polygon nodes and attributes values from polys and integration into the new GeoDataFrame
# for index, row in polys.iterrows():
#     for j in list(row['geometry'].exterior.coords):
#         with open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.csv", "a") as f:
#             f.write(str(j[0]) + ',' + str(j[1]) + ',' + str(row['DRVAL1']) + '\n')
# with open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.vrt", "w") as f:
#     f.write('''<OGRVRTDataSource>
#     <OGRVRTLayer name="xyz">
#         <SrcDataSource relativeToVRT="1">E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.csv</SrcDataSource>
#         <LayerSRS>WGS84</LayerSRS>
#         <GeometryType>wkbPoint</GeometryType>
#         <GeometryField encoding="PointFromColumns" x="x" y="y" z="z"/>
#     </OGRVRTLayer>
# </OGRVRTDataSource>''')
#
# nn = gdal.Grid("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/invdistnn_xyz.tif", "E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.vrt", zfield='z' , algorithm="invdistnn")
# nn = None




#CONVERT SOUNDINGS TO RASTER!!! end up with a + need to multiply by -1

#need to cookie cutter out the Dredge area turn dredge area intoa  raster than add that into the raster
# from osgeo import gdal
# import geopandas as gpd
# import geopandas as gpd
# from shapely.geometry import Point
# from shapely.geometry import MultiPoint
# df = gpd.read_file(r"E:\UMD_Project\SWIM\GIS\Charts\US5NYCBG\ENC_ROOT\US5NYCBG\US5NYCBG.shp")
# with open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBF/ENC_ROOT/US5NYCBF/xyz.csv", "w") as f:
#     f.write('x,y,z\n')
# for idx, row in df.iterrows():
#     for shp in row.geometry:
#         with open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.csv", "a") as f:
#             f.write(str(shp.x)+','+str(shp.y)+','+str(shp.z)+'\n')
# polys = gpd.read_file("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/dredgeDRGARE.json")
# # copy GeoDataFrame
# points2 = polys.copy()
# points2.geometry = points2.geometry.apply(lambda x: MultiPoint(list(x.exterior.coords)))
# # new GeoDataFrame with same columns
# # Extraction of the polygon nodes and attributes values from polys and integration into the new GeoDataFrame
# for index, row in polys.iterrows():
#     for j in list(row['geometry'].exterior.coords):
#         with open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.csv", "a") as f:
#             f.write(str(j[0]) + ',' + str(j[1]) + ',' + str(row['DRVAL1']) + '\n')
# with open("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.vrt", "w") as f:
#     f.write('''<OGRVRTDataSource>
#     <OGRVRTLayer name="xyz">
#         <SrcDataSource relativeToVRT="1">E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.csv</SrcDataSource>
#         <LayerSRS>WGS84</LayerSRS>
#         <GeometryType>wkbPoint</GeometryType>
#         <GeometryField encoding="PointFromColumns" x="x" y="y" z="z"/>
#     </OGRVRTLayer>
# </OGRVRTDataSource>''')
#
# nn = gdal.Grid("E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/linear_xyz.tif", "E:/UMD_Project/SWIM/GIS/Charts/US5NYCBG/ENC_ROOT/US5NYCBG/xyz.vrt", zfield='z' , algorithm="linear")
# nn = None




# #SOUNGIND TEST
# import geopandas as gpd
# df = gpd.read_file(r"E:\UMD_Project\SWIM\GIS\Charts\US5NYCBF\ENC_ROOT\US5NYCBF\US5VA51M.shp")
# for idx, row in df.iterrows():
#     for shp in row.geometry:
#         print(shp.x,shp.y,shp.z)
#
# files = glob.glob(output_path + '*.json')
# files_there = []
# for fl in files:
#     f = open(fl)
#     json_data = json.load(f)
#     files_there.append(fl)
#
#
# file = files_there[0]
# f1 = json.load(open(os.path.join(file)))
# for name in files_there:
#     f2 = json.load(open(os.path.join(name)))
#     f1['features'].extend(f2['features'])
#
# json.dump(f1, open(os.path.join(output_path + object_types + "allcharts"+ ".json"), 'w'))
#
# for fl in files:
#     f = open(fl)
#     json_data = json.load(f)
#     files_there.append(fl)
# print(files_there)
# listbuoy = []
# for file in files_there:
#     data = json.load(open(file))
#     obj_json[obj] = data
#     print(file,data)
#     for obj_types in objects:
#         print(obj_types)
#         for obj_list in obj_json:
#             print(obj_list)
#             if obj_list == obj_types:
#                 for item in obj_json[obj_types]['features']:
#                     print(item['geometry']["coordinates"])
#                     listbuoy.append(item['geometry']["coordinates"])
#             else:
#                 print('done')
#
# for pos, item in enumerate(listbuoy):
#     if (item in listbuoy):
#         # print(listbuoy.index(x))
#         print(item)
#         f = open("buoy.ini", "w")
#         count = 0
#         for item in obj_json['BOYLAT']['features']:
#             x = str(item['geometry']['coordinates'][0])  # lat
#             print(x)
#             y = str(item['geometry']['coordinates'][1])  # long
#             f.write('Type(%s)="port"\nLAT(%s)=%s\nLONG(%s)=%s\n\n' % (
#                 str(count), str(count), str(y), str(count), str(x)))
#             count += 1
#         f.close()
#         f = open("buoy.ini", "r")
#         f.read()
#         f.close()
#         line = "Number={}\n".format(count)
#         prepend_line("buoy.ini", line)
#
#
#
# #COLORS FOR LIGHTS
# import matplotlib
# ex for Violet
# red = matplotlib.colors.to_rgb(colour_dic["['10']"])[0]*255
# green = matplotlib.colors.to_rgb(colour_dic["['10']"])[1]*255
# blue = matplotlib.colors.to_rgb(colour_dic["['10']"])[2]*255
#
