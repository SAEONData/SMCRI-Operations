#this script is used to update the feature layers included in the ESRI Dashboard for the SMCRI OIMS deployed INstruments

from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

gis = GIS(url='https://nrf-saeon.maps.arcgis.com/', username='Hayden_Wilson_SAEON', password='Croswetr#01')

def overwrite_flc(featurelayer_id, csv_path):
    featurelayerCollection = FeatureLayerCollection.fromitem(gis.content.get(featurelayer_id))
    return featurelayerCollection.manager.overwrite(csv_path)

def layer_to_df(feature_layer, index):
    fl = feature_layer.layers[index]
    return pd.DataFrame.spatial.from_layer(fl)

def retrieval_update(input_csv,date_column, days_until_retrieval):
    df = pd.read_csv(input_csv)
    df['retrieval_date'] = pd.to_datetime(df[date_column]) + timedelta(days=days_until_retrieval)
    df['days_retrieval'] = (df['retrieval_date'] - datetime.now())
    df['days_retrieval'] = df['days_retrieval']/np.timedelta64(1,'D')
    df.loc[df['days_retrieval'] >= 28, 'Retrieval_Clas'] = 1 #Due in more than 4 weeks
    df.loc[(df['days_retrieval'] < 21) | (df['days_retrieval'] >= 14), 'Retrieval_Clas'] = 3 #Due in 2 weeks
    df.loc[(df['days_retrieval'] < 14) | (df['days_retrieval'] >= 7), 'Retrieval_Clas'] = 4 #Due in 1 weeks
    df.loc[(df['days_retrieval'] < 7) | (df['days_retrieval'] >= 1), 'Retrieval_Clas'] = 5 #Due in 1 weeks
    df.loc[(df['days_retrieval'] < 1) , 'Retrieval_Clas'] = 6 # Overdue
    return df

adcp_fs = '3dce4400e0954b13b67967a5029d1435'
gtp_fs = '5758be323daf4745947f99e92e9239ca'
utr_fs = '043b6ceef102433fa2afecdbf4babda4'
ct_fs = '92dd49537c39426f98432e2890382cb5'


#overwrite the feature layer collection information with the latest information from the .csv files
# overwrite_flc(ct_fl_id,ct_csv)
# overwrite_flc(gtp_fl_id,gtp_csv)
# overwrite_flc(adcp_fl_id,adcp_csv)
# overwrite_flc(utr_fl_id,utr_csv)