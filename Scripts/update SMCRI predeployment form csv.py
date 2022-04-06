# this script reads in the data from the survey123 mooring surveys and then updates the associated .csv files and feature layers 
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# ArcGIS Online Login
gis = GIS(url='https://nrf-saeon.maps.arcgis.com/', username='Hayden_Wilson_SAEON', password='Croswetr#01')


# function to overwrite the csv file in ArcGIS Online with a new file
def updatecsv(arcgis_csv, new_csv):
    previous = gis.content.search(arcgis_csv, item_type="CSV")[0]
    return previous.update(data=new_csv)


# function to convert Feature Layer to Pandas Dataframe
def layer_to_df(feature_layer, index):
    fl = feature_layer.layers[index]
    return pd.DataFrame.spatial.from_layer(fl)


# function to convert Table Layer to Pandas Dataframe
def table_to_df(feature_layer, index):
    fl = feature_layer.tables[index]
    return pd.DataFrame.spatial.from_layer(fl)


# function to join parent feature layer dataframe information to related table dataframe, remove and rename the duplicate columns
def join_layer(related_table_df, feature_layer_df, left_join_id, right_join_id):
    droplist = ['objectid_y', 'globalid_y', 'CreationDate_y', 'Creator_y', 'EditDate_y', 'Editor_y']
    df = pd.merge(related_table_df, feature_layer_df, left_on=left_join_id, right_on=right_join_id)
    df = df.drop(columns=droplist)
    df.rename(columns={'objectid_x': 'objectid',
                       'globalid_x': 'globalid',
                       'CreationDate_x': 'CreationDate',
                       'Creator_x': 'Creator',
                       'EditDate_x': 'EditDate',
                       'Editor_x': 'Editor'}, inplace=True)
    return df

#function to calculate the retrieval date for deployments
def retrieval_update(input_df,date_column, days_until_retrieval):
    df = input_df
    df['retrieval_date'] = pd.to_datetime(df[date_column]) + timedelta(days=days_until_retrieval)
    df['days_retrieval'] = (df['retrieval_date'] - datetime.now())
    df['days_retrieval'] = df['days_retrieval']/np.timedelta64(1,'D')
    df.loc[df['days_retrieval'] >= 28, 'Retrieval_Clas'] = 1 #Due in more than 4 weeks
    df.loc[(df['days_retrieval'] < 21) | (df['days_retrieval'] >= 14), 'Retrieval_Clas'] = 3 #Due in 2 weeks
    df.loc[(df['days_retrieval'] < 14) | (df['days_retrieval'] >= 7), 'Retrieval_Clas'] = 4 #Due in 1 weeks
    df.loc[(df['days_retrieval'] < 7) | (df['days_retrieval'] >= 1), 'Retrieval_Clas'] = 5 #Due in 1 weeks
    df.loc[(df['days_retrieval'] < 1) , 'Retrieval_Clas'] = 6 # Overdue
    return df

#function to overwrite the information in the feature layers that are used for dashboarding after new data is added from survey123 
def overwrite_flc(featurelayer_id, csv_path):
    featurelayerCollection = FeatureLayerCollection.fromitem(gis.content.get(featurelayer_id))
    return featurelayerCollection.manager.overwrite(csv_path)

item = gis.content.get('76a14d217a4c44e6a0423e134eba05ac')

mooring = layer_to_df(item, 0)

########Sites processing############################
# Replace 'new' values in the site with the correct ones from the satellite_short field
sites_csv_AO = gis.content.search('815eaa7b14434781819b5a7cdecafb3b', item_type="CSV")[0]
sites_csv_AO.download('../csv_files/')
mooring.loc[mooring["site"] == 'new', 'site'] = mooring["satellite_short"]
temp_new_sites = mooring[['satellite_short', 'satellite_long']]
temp_new_sites.rename(columns={'satellite_short': 'name', 'satellite_long': 'label'}, inplace=True)
temp_new_sites.dropna(inplace=True)
sites_csv_temp = '../csv_files/sites.csv'
sites_csv_temp_df = pd.read_csv(sites_csv_temp)
combined_sites = pd.concat([sites_csv_temp_df, temp_new_sites])
combined_sites = combined_sites.drop_duplicates()
combined_sites.to_csv('../csv_files/sites.csv', index=False)
sites_csv_AO.update(data=sites_csv_temp)

#########UTR data processing#########################
utr = table_to_df(item, 0)
utr_join = join_layer(utr, mooring, 'parentglobalid', 'globalid')
utr_join.loc[utr_join['utr_deployment'].isnull(), 'utr_deployment'] = utr_join["gps_name"]
utr_join.loc[utr_join['utr_service_group'].isnull(), 'utr_service_group'] = utr_join["new_utr_service_group_long"]
utr_join['unique_id'] = (
            utr_join['cmp_type'] + '_' + utr_join['site'] + '_' + utr_join['utr_deployment'] + '_' + utr_join[
        'UTR_array_type'])
utr_recent = utr_join.sort_values('EditDate').groupby('unique_id').tail(1)

# Create UTR service Groups file and update in arcgis online
utr_service = utr_recent[['utr_service_group', 'site']]
utr_service.rename(columns={'utr_service_group': 'label', 'site': 'sites'}, inplace=True)
utr_service['name'] = utr_service['label']
utr_service = utr_service[['name', 'label', 'sites']]
utr_service = utr_service.drop_duplicates()
utr_service.to_csv('../csv_files/utr_service_groups.csv', index=False)
utr_service_csv_temp = '../csv_files/utr_service_groups.csv'
# update in ArcGIS Online
utr_service_csv_AO = gis.content.search('edd36d6a0bf84dcaa0a263648e19b25c', item_type="CSV")[0]
utr_service_csv_AO.update(data=utr_service_csv_temp)

# Create UTR deployments file and update in arcgis online
utr_deployment = utr_recent[['utr_deployment', 'station', 'utr_service_group']]
utr_deployment.rename(columns={'utr_deployment': 'name', 'station': 'label'}, inplace=True)
utr_deployment = utr_deployment.drop_duplicates()
utr_deployment.to_csv('../csv_files/utr_deployments.csv', index=False)
utr_deployment_csv_temp = '../csv_files/utr_deployments.csv'
# update in ArcGIS Online
utr_deployment_csv_AO = gis.content.search('e51ac5e3f026421bb6b1b23351a338d9', item_type="CSV")[0]
utr_deployment_csv_AO.update(data=utr_deployment_csv_temp)

# Create UTR details file and update in arcgis online
utr_details = utr_recent[['utr_deployment',
                          'station',
                          'UTR_array_type',
                          'latitude',
                          'longitude',
                          'HOBO_Pos_1',
                          'HOBO_Pos_2',
                          'HOBO_Pos_3',
                          'HOBO_Pos_4',
                          'HOBO_Pos_5',
                          'HOBO_Pos_6',
                          'HOBO_Pos_7',
                          'Accoustic_release_code',
                          'Acoustic_activation_date',
                          'deployment_date',
                          ]]
utr_details.rename(columns={'utr_deployment': 'utr_deployments', 'station': 'deployment_longname'}, inplace=True)
utr_details = utr_details.drop_duplicates()
utr_details = retrieval_update(utr_details,'Acoustic_activation_date',180)
utr_details.to_csv('../csv_files/utr_details.csv', index=False)
utr_details_csv_temp = '../csv_files/utr_details.csv'




# update in ArcGIS Online
utr_details_csv_AO = gis.content.search('de3d1768e77d4151aeeb07b44b1c5fe4', item_type="CSV")[0]
utr_details_csv_AO.update(data=utr_details_csv_temp)

######### GTP data processing ########################
gtp = table_to_df(item, 1)
gtp_join = join_layer(gtp, mooring, 'parentglobalid', 'globalid')
gtp_join.loc[gtp_join['gtp_deployment'].isnull(), 'gtp_deployment'] = gtp_join["gtp_gps_name"]
gtp_join.loc[gtp_join['gtp_service_group'].isnull(), 'gtp_service_group'] = gtp_join["new_gtp_service_group_name"]
gtp_join['unique_id'] = (gtp_join['cmp_type'] + '_' + gtp_join['site'] + '_' + gtp_join['gtp_deployment'])
gtp_recent = gtp_join.sort_values('EditDate').groupby('unique_id').tail(1)

gtp_service = gtp_recent[['gtp_service_group', 'site']]
gtp_service.rename(columns={'gtp_service_group': 'label', 'site': 'sites'}, inplace=True)
gtp_service['name'] = gtp_service['label']
gtp_service = gtp_service[['name', 'label', 'sites']]
gtp_service = gtp_service.drop_duplicates()
gtp_service.to_csv('../csv_files/gtp_service_groups.csv', index=False)
gtp_service_csv_temp = '../csv_files/gtp_service_groups.csv'
# update in ArcGIS Online
gtp_service_csv_AO = gis.content.search('327f8d8524974978a530512fe8d7bb07', item_type="CSV")[0]
gtp_service_csv_AO.update(data=gtp_service_csv_temp)

gtp_deployment = gtp_recent[['gtp_deployment', 'gtp_station', 'gtp_service_group']]
gtp_deployment.rename(columns={'gtp_deployment': 'name', 'gtp_station': 'label'}, inplace=True)
gtp_deployment = gtp_deployment.drop_duplicates()
gtp_deployment.to_csv('../csv_files/gtp_deployments.csv', index=False)
gtp_deployment_csv_temp = '../csv_files/gtp_deployments.csv'
# update in ArcGIS Online
gtp_deployment_csv_AO = gis.content.search('fa7444a630794ad7886d1d4607a81d3a', item_type="CSV")[0]
gtp_deployment_csv_AO.update(data=gtp_deployment_csv_temp)
##Note to hayden - need to update the above part to include the links to media that gets uploaded.

gtp_details = gtp_recent[['gtp_deployment',
                          'gtp_latitude',
                          'gtp_longitude',
                          'HOBO_SN',
                          'gtp_deployment_date',
                          ]]
gtp_details.rename(
    columns={'gtp_deployment': 'gtp_deployments','gtp_latitude': 'latitude', 'gtp_longitude': 'longitude', 'gtp_deployment_date': 'deployment_date'},
    inplace=True)
gtp_details = gtp_details.drop_duplicates()
gtp_details = retrieval_update(gtp_details,'deployment_date',180)
gtp_details.to_csv('../csv_files/gtp_details.csv', index=False)
gtp_details_csv_temp = '../csv_files/gtp_details.csv'
# update in ArcGIS Online
gtp_details_csv_AO = gis.content.search('ebf9f92be981457781c78a35c907c46f', item_type="CSV")[0]
gtp_details_csv_AO.update(data=gtp_details_csv_temp)

#########ADCP data processing#########################
adcp = table_to_df(item, 2)
adcp_join = join_layer(adcp, mooring, 'parentglobalid', 'globalid')
adcp_join.loc[adcp_join['adcp_deployment'].isnull(), 'adcp_deployment'] = adcp_join["adcp_gps_name"]
adcp_join['unique_id'] = (adcp_join['cmp_type'] + '_' + adcp_join['site'] + '_' + adcp_join['adcp_deployment'])
adcp_recent = adcp_join.sort_values('EditDate').groupby('unique_id').tail(1)

# #Create UTR deployments file and update in arcgis online
adcp_deployment_temp = '../csv_files/adcp_deployments.csv'
adcp_deployment_temp_df = pd.read_csv(adcp_deployment_temp)
adcp_deployment = adcp_recent[['adcp_deployment', 'adcp_station', 'site']]
adcp_deployment.rename(columns={'adcp_deployment': 'name', 'adcp_station': 'label', 'site': 'sites'}, inplace=True)
adcp_deployment_comb = pd.concat([adcp_deployment, adcp_deployment_temp_df])
adcp_deployment_comb = adcp_deployment_comb.drop_duplicates()
adcp_deployment.to_csv('../csv_files/adcp_deployments.csv', index=False)
adcp_deployment_csv_temp = '../csv_files/adcp_deployments.csv'
# update in ArcGIS Online
adcp_deployment_csv_AO = gis.content.search('d7534ae118114fe5b06f49ef06f439d7', item_type="CSV")[0]
adcp_deployment_csv_AO.update(data=adcp_deployment_csv_temp)

# Create ADCP details file and update in arcgis online
adcp_details = adcp_recent[['adcp_deployment',
                            'adcp_station',
                            'ADCP_type',
                            'adcp_latitude',
                            'adcp_longitude',
                            'adcp_beacon_IMEI',
                            'adcp_acoustic_release_code',
                            'adcp_acoustic_activation_date',
                            'adcp_deployment_date',
                            ]]
adcp_details.rename(columns={'adcp_deployment': 'adcp_deployments',
                             'adcp_station': 'adcp_longname',
                             'adcp_latitude': 'latitude',
                             'adcp_longitude': 'longitude',
                             'adcp_beacon_IMEI': 'beacon_IMEI',
                             'adcp_acoustic_release_code': 'acoustic_release_code',
                             'adcp_acoustic_activation_date': 'acoustic_activation_date',
                             'adcp_deployment_date': 'deployment_date'}
                    , inplace=True)
adcp_details = adcp_details.drop_duplicates()
adcp_details = retrieval_update(adcp_details,'deployment_date',180)
adcp_details.to_csv('../csv_files/adcp_details.csv', index=False)
adcp_details_csv_temp = '../csv_files/adcp_details.csv'
# update in ArcGIS Online
adcp_details_csv_AO = gis.content.search('32c8b08756cc49d08a1ad30527229409', item_type="CSV")[0]
adcp_details_csv_AO.update(data=adcp_details_csv_temp)

#########CT data processing#########################
ct = table_to_df(item, 3)
ct_join = join_layer(ct, mooring, 'parentglobalid', 'globalid')

# replace tributaries with actual tributary names
ct_join.loc[ct_join["ct_place"] == 'tributary', "ct_place"] = ct_join['tributary_shortname']
ct_join.loc[ct_join["ct_place"].isnull(), "ct_place"] = ct_join["ct_deployment"].str.split('_').str[1]
ct_join.loc[ct_join["new_ct_service_group"] == 'yes', 'ct_service_group'] = ct_join["new_ct_service_group_name"]
ct_join['ct_deployment'] = ct_join["ct_service_group"] + '_' + ct_join['ct_place']
ct_join['unique_id'] = (ct_join['cmp_type'] + '_' + ct_join['site'] + '_' + ct_join['ct_deployment'])
ct_recent = ct_join.sort_values('EditDate').groupby('unique_id').tail(1)

ct_service = ct_recent[['ct_service_group', 'site']]
ct_service.rename(columns={'ct_service_group': 'label', 'site': 'sites'}, inplace=True)
ct_service['name'] = ct_service['label']
ct_service = ct_service[['name', 'label', 'sites']]
ct_service = ct_service.drop_duplicates()
ct_service.to_csv('../csv_files/ct_service_groups.csv', index=False)
ct_service_csv_temp = '../csv_files/ct_service_groups.csv'
# update in ArcGIS Online
ct_service_csv_AO = gis.content.search('44f315b76bd84216b7ddcd5a43fa4d79', item_type="CSV")[0]
ct_service_csv_AO.update(data=ct_service_csv_temp)

ct_deployment = ct_recent[['ct_deployment', 'ct_place', 'ct_service_group']]
ct_deployment.rename(columns={'ct_deployment': 'name', 'ct_place': 'label'}, inplace=True)
ct_deployment = ct_deployment.drop_duplicates()
ct_deployment.to_csv('../csv_files/ct_deployments.csv', index=False)
ct_deployment_csv_temp = '../csv_files/ct_deployments.csv'
# update in ArcGIS Online
ct_deployment_csv_AO = gis.content.search('01ad4ed101664e409ec800f449f00950', item_type="CSV")[0]
ct_deployment_csv_AO.update(data=ct_deployment_csv_temp)

ct_details = ct_recent[['ct_deployment',
                        'ct_latitude',
                        'ct_longitude',
                        'ct_serial',
                        'ct_battery',
                        'ct_deployment_date'
                        ]]
ct_details.rename(columns={'ct_deployment': 'ct_deployments',
                           'ct_latitude': 'latitude',
                           'ct_longitude': 'longitude',
                           'ct_battery': 'battery',
                           'ct_deployment_date': 'deployment_date'
                           }, inplace=True)
ct_details = ct_details.drop_duplicates()
ct_details = retrieval_update(ct_details,'deployment_date',180)
ct_details.to_csv('../csv_files/ct_details.csv', index=False)
ct_details_csv_temp = '../csv_files/ct_details.csv'
# update in ArcGIS Online
ct_details_csv_AO = gis.content.search('990dc76acca34334af8be10b9e014f66', item_type="CSV")[0]
ct_details_csv_AO.update(data=ct_details_csv_temp)

########## Update the feature Layer Collections for each of the deployment types #########
adcp_fs = '3dce4400e0954b13b67967a5029d1435'
gtp_fs = '5758be323daf4745947f99e92e9239ca'
utr_fs = '043b6ceef102433fa2afecdbf4babda4'
ct_fs = '92dd49537c39426f98432e2890382cb5'

overwrite_flc(ct_fs,ct_details_csv_temp)
overwrite_flc(gtp_fs,gtp_details_csv_temp)
overwrite_flc(adcp_fs,adcp_details_csv_temp)
overwrite_flc(utr_fs,utr_details_csv_temp)