
import pandas as pd
from pymongo import MongoClient
import numpy as np
import ast
import pandas as pd
from fuzzywuzzy import process


class data_processer(object):
    """docstring for data_processing making splits."""
    def __init__(self, artist_df= None, events_df_raw = None):

        self.artists_df = artist_df
        self.events_df_raw = events_df_raw
        self.events_df = None
        self.venues_df = None
        self.name_to_id = None
        self.id_to_name = None
        self.id_to_lat = None
        self.id_to_lng = None

    def fit(self):
        if self.artists_df is None:
            self.artists_df = self.make_artist_df()
        if self.events_df_raw is None:
            self.events_df_raw = self.make_events_df_raw(self.artists_df)
        self.venues_df = self.make_venue_df(self.events_df_raw)
        print('venues info')
        print(self.venues_df.info())
        print('events_raw')
        print(self.events_df_raw.info())
        self.events_df = self.make_events_df(self.events_df_raw, self.venues_df)
        print('events_raw')
        print(self.events_df_raw.info())

    def return_tables(self):
        return self.artists_df,\
         self.venues_df, self.events_df, self.events_df_raw

    def make_artist_df(self, colection = 'artist'):
        '''THIS FUNCTION COMPLIES THE ARTIST DATA FRAME FROM THE MOGO DATABASE
        THAT WAS COMPILED FROM AN API AND WEBSCRAPING'''
        mc = MongoClient()
        capstone_db = mc['bit_scraping']
        #artist_names  = capstone_db['artist_names']
        artist_info = capstone_db['artist']
        data_raw = pd.DataFrame(list(artist_info.find()))
        data = data_raw.rename({'id':'artist_id', 'image_url':'artist_image'\
                     ,'name':'artist_name', 'thumb_url': 'artist_thumb',
                     'url':'artist_url', 'facebook_page_url': 'artist_facebook'}, axis = 1).copy()

        artist_df = data.astype({'artist_id':int}, inplace=True)
        return artist_df

    def make_events_df_raw(self, artist_df, states = ['WA', 'OR','ID']):
        '''THIS FUNCTION MAKES A RAW DATA FRAME IT IS USED THIS RAW DataFrame
        IS THE PASED THROUGH THE ____ FUNCTION TO MAKE A VENUES DATAFRAME AND
        A FINISHED EVENTS DATA FRAME. WHEN DOING A TRIAN TEST SPLIT SPLIT AFTER
        THIS FUNCTION THE VENUE ID'S WILL NOT BE HERE BUT A UNIQUE NAME CALLED
        venueidentifer'''

        events_raw = artist_df.copy()
        events_raw = events_raw[~artist_df.tour.isnull()]
        print('1')
        #event_raw['tour'] = event_raw.tour.apply(lambda x: ast.literal_eval(x))
        df2 =self._splitDataFrameList(events_raw, 'tour')
        print('2')
        df3 = df2.tour.apply(pd.Series)
        print('3')
        df3.rename({'id':'event_id', 'url':'event_url'}, axis = 'columns', inplace = True)
        df4 = df3.venue.apply(pd.Series)
        print('4')
        df4.rename({'name':'venue_name',}\
                        ,axis = 'columns', inplace=True)
        df5 = pd.concat([df2,df3,df4], axis = 1)
        df5.drop(columns = ['tour','venue'], inplace=True)
        df6 = df5.astype({'event_id':int, 'latitude':float, 'longitude':float})
        df6 = df6[df6['region'].isin(states)]
        df6.datetime = pd.to_datetime(df6.datetime)
        event_df = df6[~df6.venue_name.isnull()]
        #return event_df
        event_df = self._pre_process_venue_names(event_df)
        event_df = event_df.loc[:,~event_df.columns.duplicated()]

        for state in states:
            #return event_df[event_df['region'].isin(states)]['city']
            citys = set(event_df[event_df['region'].isin(states)]['city'])
            for city in citys:
                event_df = self._convert_city_venue_name(event_df, state, city)


        event_df['venueidentifer'] = event_df['venue_name'] +' '+event_df['city']\
        +' '+event_df['region']+' '+event_df['country']
        event_df.rename({'bio':'artist_bio', 'genre':'artist_genre'}\
                        ,axis = 'columns', inplace=True)
        event_df.drop('band_name', axis =1,inplace = True)
        return event_df

    def _splitDataFrameList(self, df,target_column):
        '''THIS FUNCTION IS USED TO SPLIT THE ARTIST TOUR INTO ROWS FOR THE
        RAW EVENTS DATA_FRAM'''

        new_rows = []
        df.apply(self._splitListToRows,axis=1,args = (new_rows,target_column))
        new_df = pd.DataFrame(new_rows)
        return new_df

    def _splitListToRows(self, row,row_accumulator,target_column):
        split_row = row[target_column]
        for s in split_row:
            new_row = row.to_dict()
            new_row[target_column] = s
            row_accumulator.append(new_row)

    def _pre_process_venue_names(self, events):
        '''THIS FUNCTION TAKES IS CALLED BY make_events_df_raw THE VENUE NAMES
        AND PREPARSE THEM FOR
        TO BE '''

        events['vn_original'] = events['venue_name'].copy()
        events['venue_name'] = events['venue_name'].str.lower()
        events['venue_name'] = events['venue_name'].str.replace('[^\w\s]','').str.strip()
        stopwords = ['the', 'with', 'guest']
        events['venue_name'] = events['venue_name'].apply(self._remove_stopword)
        return events

    def _remove_stopword(self, text):
        '''THIS FUNCTION IS CALLED pre_porcess_venue_names TO REMOVE stopwords
        FROM THE VENUE NAMES'''
        stopwords = ['the', 'with', 'guest']
        return ' '.join(word for word in text.split() if word and word not in stopwords)

    def _convert_city_venue_name(self, events_raw, state, city, threshold = 86):
        '''THIS FUNCTION  IS CALLED BY make_events_df_raw TO MAKE
        UNIQUE VENUE NAMES ie. THE SHOWBOX and THE SHOWBOX IN SEATTLE should
        all be SHOWBOX
        IT TAKES A LONG TIME TO RUN SO DON'T DO IT'''

        state_events = events_raw[events_raw['region'] == state]
        city_events = state_events[state_events['city'] == city]
        venue_names = sorted(set(city_events['venue_name'].values))
        venue_names.sort(key=len)
        dct = {}
        if len(venue_names) >100:
            print(city)
        while len(venue_names) != 0:
            lst = process.extract(venue_names[0], venue_names)
            value = lst[0][0]
            for t in lst:
                if t[1] > 86:
                    dct[t[0]]=value
            venue_names = [x for x in venue_names if x not in dct]

        for i, row in city_events.iterrows():
                    venue_name = row['venue_name']
                    if venue_name in dct:
                        events_raw.at[i, 'venue_name'] = dct[venue_name]
        return events_raw


    def make_venue_df(self, venues_raw):
        'THIS FUNCTION MAKES A VENUES DATA FRAME WITH UNIQUE IDS'

        df_raw1 = venues_raw[['venueidentifer','venue_name','country',\
                   'region','city', 'artist_genre',\
                   'artist_bio','latitude', 'longitude']]
        df_raw1.artist_bio.fillna('', inplace= True)
        df_raw1.artist_genre.fillna('', inplace = True)
        df_raw2 = df_raw1.groupby(['venueidentifer','venue_name','country','region','city']).\
                                    agg({'artist_genre':[list], 'artist_bio':[list],\
                                    'latitude':['mean'], 'longitude':['mean']})
        venue_data = df_raw2.reset_index()
        venue_data['venue_id'] = venue_data.index
        venue_data.columns = venue_data.columns.droplevel(1)
        venue_data.rename({'artist_bio':'venue_bio', 'artist_genre':'venue_genre'}\
                        ,axis = 'columns', inplace=True)
        venue_data['venue_bio'] = venue_data['venue_bio'].apply(lambda x:\
                                                                ' '.join(x))
        venue_data['venue_genre'] = venue_data['venue_genre'].apply(lambda x:\
                                                                ' '.join(x))
        venue_data['venue_bio'] = venue_data['venue_bio']\
                                            .apply(lambda x: self._make_nans(x))
        venue_data['venue_genre'] = venue_data['venue_genre']\
                                            .apply(lambda x: self._make_nans(x))
        venue_data = venue_data[~venue_data.latitude.isnull()]
        if self.id_to_name is None:
            self.id_to_name = dict(zip(venue_data.venue_id, venue_data.venueidentifer))
            self.name_to_id = dict(zip(venue_data.venueidentifer, venue_data.venue_id))
        else:
            venue_data = self._add_venue_id_to_dataframe(venue_data)
        if self.id_to_lat is None:
            self.id_to_lat = dict(zip(venue_data.venue_id,venue_data.latitude))
            self.id_to_lng = dict(zip(venue_data.venue_id,venue_data.longitude))
        else:
            venue_data['latitude'] = (venue_data.venue_id).map(self.id_to_lat)
            venue_data['longitude'] = (venue_data.venue_id).map(self.id_to_lng)


        return venue_data

    def _make_nans(self, x):
        if x == '':
            return None
        else:
            return x

    def _add_venue_id_to_dataframe(self, events_raw):
        '''THIS FUNCTION PUTS IDS ON THE VENUES DATA FRAME'''
        events_raw['venue_id'] = (events_raw.venueidentifer).map(self.name_to_id)
        return events_raw

    def make_events_df(self, events_raw, venues_df):
        '''CALL THIS FUNCTION ON THE VENUE DATAFRAME TO GET A CONVERSION DICTIONARYS
        OF venue_id TO venueidentifer AND THE REVERSE'''


        #id_to_name, name_to_id = make_conversion_dictionarys(venues_df)
        events = self._add_venue_id_to_dataframe(events_raw)
        events = events[['artist_id','artist_bio','artist_genre','venue_id',\
                            'artist_name','home_town','event_id','event_url']]
        #id_to_name, name_to_id = make_conversion_dictionarys(venues_df)
        #events = add_venue_id_to_events(events, name_to_id)
        #return events
        events = events.join(venues_df.set_index('venue_id'),\
                            on='venue_id', how = 'inner')
        events.venue_id = events.venue_id.astype(int)
        self.events_df_raw = self._add_venue_id_to_dataframe(self.events_df_raw)
        self.events_df_raw['latitude'] = (self.events_df_raw.venue_id).map(self.id_to_lat)
        self.events_df_raw['longitude'] = (self.events_df_raw.venue_id).map(self.id_to_lng)
        self.events_df_raw = self.events_df_raw[~self.events_df_raw.latitude.isnull()]
        return events

    def train_test_split(self, prcnt):
        events_sorted = self.events_df_raw.sort_values(by = ['datetime'])
        split = int(len(events_sorted)*prcnt)
        train_events_raw = events_sorted[0:split]
        test_events_raw = events_sorted[split+1:]
        train_venues = self.make_venue_df(train_events_raw)
        train_events = self.make_events_df(train_events_raw, train_venues)
        return train_events, train_venues, test_events_raw
