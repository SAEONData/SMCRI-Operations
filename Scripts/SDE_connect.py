# import arcpy
# from arcgis.gis import GIS
# 
# #ArcGIS Online Login
# source = GIS(url='https://nrf-saeon.maps.arcgis.com', username= 'Hayden_Wilson_SAEON', password= 'Croswetr#01')
# 
# #Service Url for the Feature Service
# infeatures = "https://services7.arcgis.com/jbdCPRrwkIrZb0KZ/arcgis/rest/services/Deployed_Instruments/FeatureServer/0"
# 
# #Set the path for the copied data 
# outpath = r"C:\Users\hayden\Documents\ArcGIS\Projects\MyProject\192.168.120.55, 5433.sde"
# outfeature = 'test'
# 
# #Copy the Data
# arcpy.FeatureClassToFeatureClass_conversion(infeatures, outpath,outfeature)

# Import libraries
import arcpy
import arcgis
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
from arcgis import features
import pandas as pd
# Connect to the GIS
source = GIS(url='https://mondi.maps.arcgis.com', username='MondiSA', password='MondiSA2016')

my_content = gis.content.search(query="owner:" + gis.users.me.username,
                                item_type="Feature Layer",
                                max_items=15)

my_content

# 
# 
# # Grab the hosted table using the id of the csv
# old_csv = GIS.content.search("NC_Compts", item_type = "CSV")[0]
# 
# # Create a collection of feature classes and tables from the csv
# old_csv.update(data=r'C:\Users\hayden\Downloads\nc_compts.csv')

