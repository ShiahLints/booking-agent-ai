import pandas as pd
from pymongo import MongoClient
import pymongo
import numpy as np





def clean_event_data(list_of_states):
    mc = MongoClient()
    capstone_db = mc['bit_scraping']
    event_info  = capstone_db['events']
    data = pd.DataFrame(list(event_info.find()))


    #pull of the venue info
    #and add it to the dataframe
    #remove the venue column
    venue_data = pd.DataFrame(list(data['venue']))
    venue_data.rename(columns = {'name':'venue_name', 'id':'event_id', }, inplace = True )
    df = pd.concat([data, venue_data], axis = 1)
    df.drop(labels = 'venue',axis = 1, inplace = True)
    #drop the places where langitude is null
    df = df[~df.latitude.isnull()]
    df = df[df['region'].isin(list_of_states)]
    df['venue_id'] = df['venue_name']+' '+df['city']+' '+df['region']
    #make a venue id column
    index_list = list(np.unique(df['venue_id']))
    ids = []
    for value in df['venue_id']:
        #print(value)
        ids.append(index_list.index(value))
    df['venue_id'] = ids
    df.rename(columns = {'id':'event_id'}, inplace = True)
    df['artist_id'] = df.artist_id.astype(int)
    df['event_id'] = df.event_id.astype(int)

    return df

def make_ratings_matrix(data):
    ratings_matrix = data[['artist_id', 'venue_id', 'event_id']]
    groupby = ratings_matrix.groupby(by = ['artist_id', 'venue_id'], as_index=False)
    ratings_matrix = pd.DataFrame(groupby.count())
    ratings_matrix.rename(columns = {'event_id':'num_shows'}, inplace = True)
    return ratings_matrix
