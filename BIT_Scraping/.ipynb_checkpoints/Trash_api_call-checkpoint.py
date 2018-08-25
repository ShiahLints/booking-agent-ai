"""

This code gathers all the data together and stores it in a mongodb:
In order to run this notebook. First a list of Citys must be selected
And from there the BIT website must be scraped city by city to generate
a set of bands.

"""

import pandas as pd
import re
from pymongo import MongoClient
import requests



mc = MongoClient()  # Connect to the MongoDB server using default settings
capstone_db = mc['stranger_scraping']  # Use (or create) a database called 'election_predictions'
location_info = capstone_db['events']

#this was my attempt to gather the venue data right after the call
#it has missing values though an will be easier to deal with
#after the fact

'''def clean_event_to_store(e):
    #print(e)
    e['venue_gps'] = e['venue']['latitude'] +','+ e['venue']['longitude']
    e['country'] = e['venue']['country']
    e['region'] = e['venue']['region']
    e['city'] = e['venue']['city']
    e['venue_name'] = e['venue']['name']
    e['venue_long'] = e['venue']['longitude']
    e['venue_lat'] = e['venue']['latitude']
    del e['venue']

    return e'''

def api_tour_call(band):

    # these next lines of code remove chars the the BIT api does not like
    band_name = band
    band_name = band_name.replace(' ','%20')
    band_name = band_name.replace( '/', '%252F')
    band_name = band_name.replace( '?', '%253F')
    band_name = band_name.replace( '*', '%252A')
    band_name = band_name.replace( '"', '%2&C')

    #print('api_call', band_name)
    #ther are a small number of bands with names to long for the api
    #these cases are just droped from the model

    try:
        result = requests.get("https://rest.bandsintown.com/artists/" +
                            band_name +
                          "/events?app_id=2eafc16df6cb4f3db3bb365ca0d91f6e",)

        result = result.json()
        for event in result:
            event['band_name'] = band

        return result
    except:
        return band



def STEP_TWO_store_event_data(file_path):
    band_names = pd.read_csv(file_path)['band_names']
    bad_bands = []
    c = MongoClient()
    capstone_db = mc['bit_scraping']
    event_info  = capstone_db['events']
    for i, band in enumerate(band_names):
        if i%20 == 1:
            print('storing tour', i , 'of', len(band_names))
        tour = api_tour_call(band)
        if tour == band:
            bad_bands.append(band)
        else:
            for j, event in enumerate(tour):
                event_info.update_one({'id':event['id']},
                                     {"$set": event}, upsert=True)
    return bad_bands
