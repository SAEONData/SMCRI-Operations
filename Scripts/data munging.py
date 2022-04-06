#this script reads in the data from the survey123 and joins related tables
from arcgis.gis import GIS
import pandas as pd

#ArcGIS Online Login
gis = GIS(url='https://nrf-saeon.maps.arcgis.com/', username= 'Hayden_Wilson_SAEON', password= 'Croswetr#01')

#function to overwrite the csv file in ArcGIS Online with a new file
def updatecsv(arcgis_csv, new_csv):
    previous = gis.content.search(arcgis_csv, item_type="CSV")[0]
    return previous.update(data=new_csv)

#function to convert Feature Layer to Pandas Dataframe
def layer_to_df(feature_layer, index):
    fl = feature_layer.layers[index]
    return pd.DataFrame.spatial.from_layer(fl)

#function to convert Table Layer to Pandas Dataframe
def table_to_df(feature_layer, index):
    fl = feature_layer.tables[index]
    return pd.DataFrame.spatial.from_layer(fl)

#function to join parent feature layer dataframe information to related table dataframe, remove and rename the duplicate columns
def join_layer(related_table_df,feature_layer_df,  left_join_id, right_join_id):
    droplist = ['objectid_y', 'globalid_y', 'CreationDate_y', 'Creator_y', 'EditDate_y', 'Editor_y']
    df = pd.merge(related_table_df, feature_layer_df,left_on = left_join_id, right_on=right_join_id)
    df = df.drop(columns=droplist)
    df.rename(columns={'objectid_x':'objectid',
                       'globalid_x': 'globalid',
                       'CreationDate_x': 'CreationDate',
                       'Creator_x': 'Creator',
                       'EditDate_x':'EditDate',
                       'Editor_x': 'Editor'},inplace=True)
    return df

#function to take the values from a dataframe and then take only the most recent records
def recent_entries(dataframe, date_column, unique_id):
    df = dataframe.sort_values(date_column).groupby(unique_id).tail(1)
    return df

############___________Example________________ ################

# 1. get the feature layer from ArcGIS Online
feature_collection = gis.content.get('76a14d217a4c44e6a0423e134eba05ac')
print(feature_collection)

# 2. Convert the feature layer into a dataframe (0 below is the index for the feature data in the feature collection)
feature_df = layer_to_df(feature_collection,0)
print("the field names for the feature dataframe are:")
print(feature_df.columns)
# 3. Convert the table layer into a dataframe (0 below is because its the first table of the feature collection)
table_df = table_to_df(feature_collection,0)
print("the field names for the table dataframe are:")
print(table_df.columns)

# 4. Join them on the feature layer globalid and the table parentglobalid and drop the columns from the columnlist
joined_df = join_layer(table_df,feature_df,'parentglobalid', 'globalid')
print("the field names for the table dataframe are:")
print(joined_df.columns)

# 5. do some calculations to create new field values - these are similar to 'where' clauses. so where a row is null or 'new', specify the value from another column
joined_df.loc[joined_df['utr_deployment'].isnull(),'utr_deployment'] = joined_df["gps_name"]
joined_df.loc[joined_df['utr_service_group'].isnull(),'utr_service_group'] = joined_df["new_utr_service_group_long"]
joined_df.loc[joined_df["site"] == 'new','site'] = joined_df["satellite_short"]

# 6. Create a grouping id
joined_df['unique_id'] = (joined_df['cmp_type'] + '_' + joined_df['site'] + '_' + joined_df['utr_deployment'] + '_' + joined_df['UTR_array_type'])

# 7. Create a dataframe with only the most recent values
recent_values_df = recent_entries(joined_df, 'EditDate', 'unique_id')

# 8. Export the recent values dataframe to a csv
recent_values_df.to_csv(r'C:\Data\Elwandle Operational information\CSV Lists\test_list4.csv')

# 9 publish the data to a feature layer in arcgis online
lyr = recent_values_df.spatial.to_featurelayer('recent_values_df', folder='test')
