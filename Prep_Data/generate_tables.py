
import pandas as pd
from pymongo import MongoClient
import numpy as np
import ast
import pandas as pd
from fuzzywuzzy import process


def make_artist_df(colection = 'artist'):
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


def make_events_df_raw(artist_df, states):
    '''THIS FUNCTION MAKES A RAW DATA FRAME IT IS USED THIS RAW DataFrame
    IS THE PASED THROUGH THE ____ FUNCTION TO MAKE A VENUES DATAFRAME AND
    A FINISHED EVENTS DATA FRAME. WHEN DOING A TRIAN TEST SPLIT SPLIT AFTER
    THIS FUNCTION THE VENUE ID'S WILL NOT BE HERE BUT A UNIQUE NAME CALLED
    venueidentifer'''
    def splitDataFrameList(df,target_column):
        '''THIS FUNCTION IS USED TO SPLIT THE ARTIST TOUR INTO ROWS FOR THE
        RAW EVENTS DATA_FRAM'''

        def splitListToRows(row,row_accumulator,target_column):
            split_row = row[target_column]
            for s in split_row:
                new_row = row.to_dict()
                new_row[target_column] = s
                row_accumulator.append(new_row)
        new_rows = []
        df.apply(splitListToRows,axis=1,args = (new_rows,target_column))
        new_df = pd.DataFrame(new_rows)
        return new_df

    def pre_process_venue_names(events):
        '''THIS FUNCTION TAKES IS CALLED BY make_events_df_raw THE VENUE NAMES
        AND PREPARSE THEM FOR
        TO BE '''
        def remove_stopword(text):
            '''THIS FUNCTION IS CALLED pre_porcess_venue_names TO REMOVE stopwords
            FROM THE VENUE NAMES'''
            stopwords = ['the', 'with', 'guest']
            return ' '.join(word for word in text.split() if word and word not in stopwords)

        events['vn_original'] = events['venue_name'].copy()
        events['venue_name'] = events['venue_name'].str.lower()
        events['venue_name'] = events['venue_name'].str.replace('[^\w\s]','').str.strip()
        stopwords = ['the', 'with', 'guest']
        events['venue_name'] = events['venue_name'].apply(remove_stopword)
        return events

    def convert_city_venue_name(events_raw, state, city, threshold = 86):
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

    event_raw = artist_df.copy()
    event_raw = event_raw[~artist_df.tour.isnull()]
    print('1')
    #event_raw['tour'] = event_raw.tour.apply(lambda x: ast.literal_eval(x))
    df2 =splitDataFrameList(event_raw, 'tour')
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
    event_df = pre_process_venue_names(event_df)
    event_df = event_df.loc[:,~event_df.columns.duplicated()]
    for state in states:
        #return event_df[event_df['region'].isin(states)]['city']
        citys = set(event_df[event_df['region'].isin(states)]['city'])
        for city in citys:
            event_df = convert_city_venue_name(event_df, state, city)


    event_df['venueidentifer'] = event_df['venue_name'] +' '+event_df['city']\
    +' '+event_df['region']+' '+event_df['country']
    event_df.rename({'bio':'artist_bio', 'genre':'artist_genre'}\
                    ,axis = 'columns', inplace=True)
    event_df.drop('band_name', axis =1,inplace = True)
    return event_df


def make_venue_df(data):
    'THIS FUNCTION MAKES A VENUES DATA FRAME WITH UNIQUE IDS'

    def make_nans(x):
        if x == '':
            return None
        else:
            return x

    df_raw1 = data[['venueidentifer','venue_name','country',\
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
                                        .apply(lambda x: make_nans(x))
    venue_data['venue_genre'] = venue_data['venue_genre']\
                                        .apply(lambda x: make_nans(x))
    venue_data = venue_data[~venue_data.latitude.isnull()]
    return venue_data

def make_conversion_dictionarys(venue_df):
    '''CALL THIS FUNCTION ON THE VENUE DATAFRAME TO GET A CONVERSION DICTIONARYS
    OF venue_id TO venueidentifer AND THE REVERSE'''
    id_to_name = dict(zip(venue_df.venue_id,venue_df.venueidentifer))
    name_to_id = dict(zip(venue_df.venueidentifer,venue_df.venue_id))
    #print(name_to_id)
    return id_to_name, name_to_id

def add_venue_id_to_events(events_raw, name_to_id):
    '''THIS FUNCTION PUTS IDS ON THE VENUES DATA FRAME'''
    events_raw['venue_id'] = (events_raw.venueidentifer).map(name_to_id)
    return events_raw

def make_events_df(events_raw, venues_df):
    '''CALL THIS FUNCTION ON THE VENUE DATAFRAME TO GET A CONVERSION DICTIONARYS
    OF venue_id TO venueidentifer AND THE REVERSE'''
    def add_venue_id_to_events(events_raw, name_to_id):
        '''THIS FUNCTION PUTS IDS ON THE VENUES DATA FRAME'''
        events_raw['venue_id'] = (events_raw.venueidentifer).map(name_to_id)
        return events_raw

    id_to_name, name_to_id = make_conversion_dictionarys(venues_df)
    events = add_venue_id_to_events(events_raw, name_to_id)
    events = events[['artist_id','artist_bio','artist_genre','venue_id',\
                        'artist_name','home_town','event_id','event_url']]
    #id_to_name, name_to_id = make_conversion_dictionarys(venues_df)
    #events = add_venue_id_to_events(events, name_to_id)
    #return events
    return events
    events = events.join(venues_df.set_index('venue_id'), on='venue_id', how = 'inner')
    return events



def generate_data_from_colection(artist_filepath, events_filepath,
                                 venue_filepath):
    '''THIS IS THE MAIN FUNCTION ON THAT TIES EVERYTHING TOGETHER'''
    artist_df = make_artist_df()
    print('Step 1')
    artist_df.to_csv(artist_filepath)
    #takes a long time because it cleans the venue names
    events_df_raw = make_events_df_raw(artist_df)
    print('Step 2')
    venue_df = make_venue_df(events_df_raw)
    print('Step 3')
    id_to_name, name_to_id =make_conversion_dictionarys(venue_df)
    print('Step 4')
    events_df = add_venue_id_to_events(events_df_raw, name_to_id)

    return artist_df, events_df, venue_df

def _convert_city_venue_name(events_df_raw, state, city, threshold = 86):
    '''THIS FUNCTION CONVERTS IS CALLED BY make_events_df_raw TO MAKE
    UNIQUE VENUE NAMES ie. THE SHOWBOX and THE SHOWBOX IN SEATTLE should
    all be SHOWBOX
    IT TAKES A LONG TIME TO RUN SO DON'T DO IT'''
    state_events = dataset[dataset['region'] == state]
    city_events = state_events[state_events['city'] == city]
    venues = set(city_events['venue_name'])
    conversion_dct = {}
    for i, venue in enumerate(venues):
        if i%40 == 0:
            print (i ,' of ',len(venues))
        alt_name, prob = process.extract(venue, venues, limit = 2)[1]
        if prob > threshold:
            if venue == alt_name:
                continue
            if len(venue) <= len(alt_name):
                if venue in conversion_dct:
                        if alt_name != conversion_dct[venue]:
                            conversion_dct[alt_name] = conversion_dct[venue]
                else:
                    conversion_dct[alt_name] = venue
            else:
                if alt_name in conversion_dct:
                    if venue != conversion_dct[alt_name]:
                        conversion_dct[venue] = conversion_dct[alt_name]
                else:
                    conversion_dct[venue] = alt_name

    for i, row in city_events.iterrows():
        venue_name = row['venue_name']
        if venue_name in conversion_dct:
            data.at[i, 'venue_name'] = conversion_dct[venue_name]

    return data
