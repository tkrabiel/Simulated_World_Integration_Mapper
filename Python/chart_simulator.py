# importing the library
import os
import S57_converter as sc
from PIL import Image
import rasterio
from pyproj import Geod
from osgeo import gdal, gdal_array
import rasterio



# giving directory name
folderdir = 'E:/UMD_Project/SWIM/GIS/Charts/'
# giving file extension
ext = ('.000')
height_eye = 21 #set height of the users eye in Meters
topobathy_dem = r"E:\UMD_Project\SWIM\GIS\Rasters\TopoBathy_DEM\small_test.tif"
xyz_file = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz"
xyz_csv = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz"
# output = r"E:\UMD_Project\SWIM\GIS\Rasters\TopoBathy_DEM"



output_path_light = "E:/UMD_Project/SWIM/GIS/json/lights/temp/"
objects_light = ['LIGHTS']
object_types_light = "Lights"
ini_output = "E:/UMD_Project/SWIM/GIS/ini/"
combined_json_outpath_light = "E:/UMD_Project/SWIM/GIS/json/lights/"
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




output_path_buoy = "E:/UMD_Project/SWIM/GIS/json/buoy/temp/"
objects_buoy = ['BOYCAR', 'BOYINB', 'BOYISD', 'BOYLAT', 'BOYSAW', 'BOYSPP']
object_types_buoy = "Buoy"
ini_output = "E:/UMD_Project/SWIM/GIS/ini/"
combined_json_outpath_buoy = "E:/UMD_Project/SWIM/GIS/json/buoy/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path_buoy, chart, objects_buoy, object_types_buoy)
json_file_path_buoy = sc.combo_json(output_path_buoy,combined_json_outpath_buoy,object_types_buoy)
sc.json_to_ini_buoy(ini_output,json_file_path_buoy)

output_path_d = "E:/UMD_Project/SWIM/GIS/json/dredge/temp/"
objects_d = ['DRGARE']
object_types_d = "dredge"
combined_json_outpath_d = "E:/UMD_Project/SWIM/GIS/json/dredge/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path_d, chart, objects_d, object_types_d)
json_file_path_d = sc.combo_json(output_path_d,combined_json_outpath_d,object_types_d)


output_path_land = "E:/UMD_Project/SWIM/GIS/json/land/temp/"
objects_land = ['LNDARE']
object_types_land = "land"
combined_json_outpath_land = "E:/UMD_Project/SWIM/GIS/json/land/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path_land, chart, objects_land, object_types_land)
json_file_path_land = sc.combo_json(output_path_land,combined_json_outpath_land,object_types_land)

output_path_extent = "E:/UMD_Project/SWIM/GIS/json/extent/temp/"
objects_extent = ['M_COVR']
object_types_extent = "extent"
combined_json_outpath_land = "E:/UMD_Project/SWIM/GIS/json/extent/"
# iterating over directory and subdirectory to get desired result
for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path_extent, chart, objects_extent, object_types_extent)
json_file_path_land = sc.combo_json(output_path_extent,combined_json_outpath_land,object_types_extent)


output_path_sound = "E:/UMD_Project/SWIM/GIS/json/sound/temp/"
objects_sound = ['SOUNDG']
object_types_sound = "sound"
ini_output = "E:/UMD_Project/SWIM/GIS/ini/"
combined_json_outpath_sound = "E:/UMD_Project/SWIM/GIS/json/sound/"
#output_path_sound = "E:/UMD_Project/SWIM/GIS/json/sound"
# iterating over directory and subdirectory to get desired result

for path, dirc, files in os.walk(folderdir):
    for name in files:
        if name.endswith(ext):
            chart = name[:-4]
            str_path = path
            sc.S57_to_json(str_path, output_path_sound, chart, objects_sound, object_types_sound)
json_file_path = sc.combo_json(output_path_sound,combined_json_outpath_sound,object_types_sound)
#print(json_file_path)
json = "sound_combined.json"
shp = combined_json_outpath_sound+"/sound.shp"
sc.json_shp(json_file_path,shp)



DRGARE_json = combined_json_outpath_d+object_types_d+"_combined.json"
LANDAREA_json = combined_json_outpath_land+object_types_land+"_combined.json"

print("DredgeJSON: "+ json_file_path_d)
#"E:\UMD_Project\SWIM\GIS\json\dredge\dredge_combined.json"
sc.S57_raster(shp, output_path_sound, xyz_file+"/")

topobathy_dem = r"E:\UMD_Project\SWIM\GIS\Rasters\TopoBathy_DEM\sound_NYC1.tif"



#extent raster


#create the raster for the land and dredge area
#dredge

str_path = r"E:\UMD_Project\SWIM\GIS\json\dredge"
json_file_name = 'dredge_combined'
extent_tif = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz\xyz.tif"
output_file_path = "E:/UMD_Project/SWIM/GIS/json/dredge/"
output_tif = "dredge.tif"
object_name = 'dredge'
z_value = 'DRVAL1'
sc.S57_shape_raster(str_path, json_file_name, extent_tif, output_file_path, output_tif, object_name, z_value)
#land
str_path = r"E:\UMD_Project\SWIM\GIS\json\land"
json_file_name = 'land_combined'
extent_tif = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz\xyz.tif"
output_file_path = "E:/UMD_Project/SWIM/GIS/json/land/"
output_tif = "land.tif"
object_name = 'land'
z_value = '1'
sc.S57_shape_raster(str_path, json_file_name, extent_tif, output_file_path, output_tif, object_name, z_value)

# Final Bathy DEM with dredge areas
bathy_dem_path = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz\xyz.tif"
output_file_path = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz/"
dredge_raster_path = "E:/UMD_Project/SWIM/GIS/json/dredge/dredge.tif"
dredge_raster_name = 'dredge.tif'
output_file_path_mask = "E:/UMD_Project/SWIM/GIS/json/dredge/"
sc.bathydem_dredge(bathy_dem_path,output_file_path,output_file_path_mask, dredge_raster_path, dredge_raster_name)

topo_dem = r"E:\UMD_Project\SWIM\GIS\Rasters\Topo_DEM\topo_dem.tif"
topo_dem_re = r"E:\UMD_Project\SWIM\GIS\Rasters\Topo_DEM\topo_dem_re.tif"
topo_dem_re_bound = r"E:\UMD_Project\SWIM\GIS\Rasters\Topo_DEM\topo_dem_re_bound.tif"
topobathy_dem = r"E:\UMD_Project\SWIM\GIS\Rasters\TopoBathy_DEM\python_topobathy_dem.tif"
bathy_dem = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz\bathy_dem.tif"
output_file_path = r"E:\UMD_Project\SWIM\GIS\Rasters\Topo_DEM"
output_tif = "topo_dem.tif"
land_mask = sc.raster_mask(output_file_path,output_tif)
land_mask_inverse = sc.raster_inverse_mask(output_file_path,output_tif)
land_mask = r"E:\UMD_Project\SWIM\GIS\Rasters\Topo_DEM\mask_topo_dem.tif"
land_mask_inverse =r"E:\UMD_Project\SWIM\GIS\Rasters\Topo_DEM\mask_inverse_topo_dem.tif"
land_mask_re = r"E:\UMD_Project\SWIM\GIS\Rasters\Topo_DEM\mask_topo_dem_re.tif"
land_mask_inverse_re =r"E:\UMD_Project\SWIM\GIS\Rasters\Topo_DEM\mask_inverse_topo_dem_re.tif"

str = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz/"
#topobathy_dem_out = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz\topobathy_dem.tif"

bathy_dem_ds = gdal.Open(bathy_dem)
dataset = rasterio.open(bathy_dem)
bbox = dataset.bounds
# # upper_left_x, upper_left_y, lower_right_x,lower_right_y =
window = (dataset.bounds[0],dataset.bounds[3],dataset.bounds[2],dataset.bounds[3])



gdal.Warp(topo_dem_re,topo_dem,dstSRS='EPSG:4326')
gdal.Warp(land_mask_re,land_mask,dstSRS='EPSG:4326')
gdal.Warp(land_mask_inverse_re,land_mask_inverse,dstSRS='EPSG:4326')
gdal.Translate(str+'land_mask_re_bound.tif', land_mask_re, projWin = bbox)
gdal.Translate(str+'mask_inverse_topo_dem_re_bound.tif', land_mask_inverse_re, projWin = bbox)
gdal.Translate(topo_dem_re_bound, topo_dem_re, projWin = bbox)

# open reference file and get resolution
referenceFile = bathy_dem
reference = gdal.Open(referenceFile, 0)  # this opens the file in only reading mode
referenceTrans = reference.GetGeoTransform()
x_res = referenceTrans[1]
y_res = -referenceTrans[5]  # make sure this value is positive
print(y_res)

# specify input and output filenames
inputFile = str+'land_mask_re_bound.tif'
outputFile = str+'land_mask_re_bound_A.tif'

# call gdal Warp
kwargs = {"format": "GTiff", "xRes": x_res, "yRes": y_res}
ds = gdal.Warp(outputFile, inputFile, **kwargs)


# specify input and output filenames
inputFile = str+'mask_inverse_topo_dem_re_bound.tif'
outputFile = str+'mask_inverse_topo_dem_re_bound_A.tif'

# call gdal Warp
kwargs = {"format": "GTiff", "xRes": x_res, "yRes": y_res}
ds = gdal.Warp(outputFile, inputFile, **kwargs)

# specify input and output filenames
inputFile = topo_dem_re_bound
outputFile = str+'topo_dem_A.tif'

# call gdal Warp
kwargs = {"format": "GTiff", "xRes": x_res, "yRes": y_res}
ds = gdal.Warp(outputFile, inputFile, **kwargs)



topo_dem_ds = gdal.Open(str+'topo_dem_A.tif')
land_mask_ds = gdal.Open(str+'land_mask_re_bound_A.tif')
land_mask_inverse_ds = gdal.Open(str+'mask_inverse_topo_dem_re_bound_A.tif')
bdem = bathy_dem_ds.GetRasterBand(1)
tdem = topo_dem_ds.GetRasterBand(1)
lm = land_mask_ds.GetRasterBand(1)
lmi = land_mask_inverse_ds.GetRasterBand(1)
bdemarr = bdem.ReadAsArray()
tdemarr = tdem.ReadAsArray()
tdemarr = tdemarr[::-1,:]
lmarr = lm.ReadAsArray()
lmarr = lmarr[::-1,:]
lmiarr = lmi.ReadAsArray()
lmiarr = lmarr[::-1,:]
data = (lmiarr * tdemarr) + (lmarr * bdemarr)
gdal_array.SaveArray(data.astype("float32"), topobathy_dem, "GTIFF", bathy_dem_ds)
print('topobathy_dem_with_dredge done!!')
#(Land Mask X Topo DEM) + (Inverse Land Mask X Bathy DEM) = TopoBathy DEM.


topobathy_dem = r"E:\UMD_Project\SWIM\GIS\Rasters\xyz\bathy_demrgb.tif"

def DEM_ini(topobathy_dem, output):
    image = Image.open(topobathy_dem)
    image.save(output + "/height.png")
    image.show()
    print("Width: ", image.width)
    print("Height: ", image.height)
    dataset = rasterio.open(topobathy_dem)
    dataset.bounds
    g = Geod(ellps='WGS84')
    # 2D distance in meters with longitude, latitude of the points
    azimuth1, azimuth2, distance_we = g.inv(dataset.bounds[0], dataset.bounds[1], dataset.bounds[2],
                                            dataset.bounds[1])  # West-East
    print(distance_we * 0.00001186)
    we = distance_we * 0.00001186
    g = Geod(ellps='WGS84')
    # 2D distance in meters with longitude, latitude of the points
    azimuth1, azimuth2, distance_sn = g.inv(dataset.bounds[0], dataset.bounds[1], dataset.bounds[2],
                                            dataset.bounds[1])  # south-north
    print(distance_sn * 0.0000118)
    sn = distance_sn * 0.0000118
    sw_point = dataset.bounds[0], dataset.bounds[1]
    print(dataset.bounds[0], dataset.bounds[1])
    with open(output + "/terrain.ini", "w") as f:
        f.write('''
Number=1

MapImage="texture.png"

HeightMap(1)="height.png"
Texture(1)="texture.png"
TerrainLong(1)=%.4f
TerrainLat(1)=%.4f
TerrainLongExtent(1)=%.3f
TerrainLatExtent(1)=%.3f
TerrainMaxHeight(1)=113
SeaMaxDepth(1)=31.5
TerrainHeightMapSize(1)=%.3f

        ''' % (sw_point[0], sw_point[1], we, sn, image.height))
    # open raster and choose band to find min, max
    raster = topobathy_dem
    gtif = gdal.Open(raster)
    srcband = gtif.GetRasterBand(1)
    # Get raster statistics
    stats = srcband.GetStatistics(True, True)
    # Print the min, max, mean, stdev based on stats index
    print("[ STATS ] =  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % (
        stats[0], stats[1], stats[2], stats[3]))

DEM_ini(topobathy_dem, folderdir)
print("done")