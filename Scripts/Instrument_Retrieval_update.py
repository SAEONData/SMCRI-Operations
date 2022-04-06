import arcpy
from datetime import datetime, timedelta
from arcgis.gis import GIS


#ArcGIS Online Login
source = GIS(url='https://nrf-saeon.maps.arcgis.com', username= 'Hayden_Wilson_SAEON', password= 'Croswetr#01')

#Service Url for the Feature Service
infeatures = "https://services7.arcgis.com/jbdCPRrwkIrZb0KZ/arcgis/rest/services/Deployed_Instruments/FeatureServer/0"

#Calculate the Retrieval Date for the Instrument as a South African Datetime
arcpy.CalculateField_management(infeatures, "Retrieval_datetime_SA_date", "(!Acoustic_activation_datetime! + timedelta(days=180)).strftime('%d/%m/%Y')", "PYTHON3")

#Calculate the Activation Date for the Instrument as a South African Datetime
arcpy.CalculateField_management(infeatures, "Acoustic_activation_SA_date", "!Acoustic_activation_datetime!.strftime('%d/%m/%Y')", "PYTHON3")

#Calculate the Days from now that the instrument needs to be retrieved
arcpy.CalculateField_management(infeatures, "Days_Retrieval","((datetime.now() - (!Acoustic_activation_datetime! + timedelta(days=180))).days)*-1", "PYTHON3")

#Classify the days Retrieval into groups for visualisation

codeblock = """
def reclass(field):
    if field >= 28:
        return 1 #green
    if field < 28 and field >= 21:
        return 2 #Yellow
    if field < 21 and field >= 14:
        return 3 #Orange
    if field < 14 and field >= 7:
        return 4
    if field < 7 and field >=1:
        return 5
    else: 
        return 6
    """
expression = "reclass(!Days_Retrieval!)"

arcpy.CalculateField_management(infeatures, "Retrieval_Class",expression, "PYTHON3", codeblock)