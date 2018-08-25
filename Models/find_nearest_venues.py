
import pandas as pd
import numpy as np
#from math import radians, cos, sin, asin, sqrt


#venues = pd.read_csv('venues_with_clean_bios.csv')

#cities = pd.read_csv('uscitiesv1.4.csv')

def haversine_np(venue_lat, venue_lon, array):

    print (venue_lat, vunue_lon)
    lat2, lon2 = array[:,0], array[:,1]
    lat1, lon1 = np.full((lon2.shape[0]),venue_lat), np.full((lon2.shape[0]),venue_lon)
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.

    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

    c = 2 * np.arcsin(np.sqrt(a))
    miles = 3959 * c
    return miles

def get_venues_in_milage_by_lat_lng(venue_lat, venue_lon, miles, df):
    array = df[~df['latitude'].isnull()][['latitude', 'longitude']].values
    miles_array = haversine_np(venue_lat, venue_lon, array)
    return df[~df['latitude'].isnull()][list(miles_array < miles)]

def get_lat_lng_of_city(city, state):
    state, city = 'WA', 'Winthrop'
    lat, lng = cities[(cities['city'] == city) & (cities['state_id']== state)][['lat','lng']].values[0]
    return lat, lng

def get_nearest_venues_by_city(city, state, milage):
    lat, lng = get_lat_lng_of_city(city, state)
    venues = get_venues_in_milage_by_lat_lng(lat, lng, milage)
    return venues
def get_nearest_venues(venue_id, train_venues, master_venues):
    venue = master_venues[master_venues['venue_id']==venue_id]
    #print((venue['venueidentifer']))
    lat, lng = venue.latitude, venue.longitude
    lat += .00001
    lng += .00001
    return find_at_least_100(lat, lng, train_venues)



def find_at_least_100(lat, lng, df):
    milage = 10
    venues = None
    len_venues = 1
    while len_venues < 100:
        venues = get_venues_in_milage_by_lat_lng(lat, lng, milage, df)
        len_venues = len(venues)
        if len_venues<100:
            milage = milage*1.25
    #if milage != 10:
        #print ('milage grew to ', milage)
    return venues
