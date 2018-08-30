
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/Users/shiahlints/galvanize/FIXGITPROBLEM/booking-agent-ai/data')
#from math import radians, cos, sin, asin, sqrt


venues = pd.read_pickle('data/master_venues_df.p')
cities = pd.read_csv('data/uscitiesv1.4.csv')

class Venue_Finder(object):
    """this class finds the nearest venues to a point. Either another
    venue or a city state"""
    def __init__(self, venues = venues, cities= cities):
        self.cities = cities
        self.venues = venues



    def get_nearest_venues_by_city(self, city, state, milage=10):
        lat, lng = self.cities[(self.cities['city'] == city) & \
        (self.cities['state_id']== state)][['lat','lng']].values[0]
        venues = self.find_venues_by_milage(lat, lng, milage)
        return venues


    def get_nearest_venues_by_venue(self, venue_id, n):
        '''used for testing'''
        if venue_id not in self.venues.venue_id.values:
            print ('This is a new venue')
        venue = self.venues[self.venues['venue_id']==venue_id]
        #print((venue['venueidentifer']))
        lat, lng = venue.latitude, venue.longitude
        nearest_venues = self.find_at_least_n(lat, lng, n)
        if venue_id not in nearest_venues.venue_id.values:
            thing_to_add = self.venues[self.venues.venue_id == venue_id]
            nearest_venues = pd.concat([nearest_venues, thing_to_add], axis = 0)
        return nearest_venues

    def find_venues_by_milage(self, lat, lng, milage = 10):
        array = self.venues[['latitude', 'longitude']].values
        miles_array = self.haversine_np(lat, lng, array)
        #return miles_array
        milage_filter = miles_array < milage
        return self.venues.iloc[milage_filter]

    def find_at_least_n_venues(self, lat, lng, n):
        array = self.venues[['latitude', 'longitude']].values
        miles_array = self.haversine_np(lat, lng, array)
        hundred_nearest = np.argsort(miles_array)[0:n]
        radius = miles_array[hundred_nearest[-1]]
        return self.venues.iloc[hundred_nearest]

    def haversine_np(self, venue_lat, venue_lng, array):

        lat2, lon2 = array[:,0], array[:,1]
        lat1, lon1 = np.full((lon2.shape[0]),venue_lat),\
                        np.full((lon2.shape[0]),venue_lng)
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
        miles_array = 3959 * c
        return miles_array
