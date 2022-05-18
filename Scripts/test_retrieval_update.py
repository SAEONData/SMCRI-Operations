import pandas as pd
from datetime import datetime, timedelta
import numpy as np

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




df = pd.read_csv(r"C:\Scheduled_Python_Scripts\SMCRI_OIMS\SMCRI-Operations\test\test_utr_details.csv")

df["Retrieval_Clas"] = pd.cut(
    x=df["days_retrieval"],
    bins=[np.NINF,1, 7, 14, 21, 28, np.inf],
    labels=[6,5,4,3,2,1]
)

print(df)