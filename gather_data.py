
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
import numpy as np
from selenium.common.exceptions import NoSuchElementException
from pymongo import MongoClient
import requests

def download_band_names(states, file_path_to_save,
                                         file_to_read_citys = 'uscitiesv1.4.csv',
                                         test = False,
                                         test_iterations = 2):
    driver = Chrome()
    result = set()
    # fist get all the towns
    towns = _get_list_of_towns(states, file_to_read_citys)
    town_urls = _convert_townlist_to_urllist(towns)
    total_scrapes = (len(towns))
    for i, town_url in enumerate(town_urls):
        if test == True and i > test_iterations:
            break
        print ('Scraping ' + str(i+1) + 'of' + str((total_scrapes)+1))
        print(town_url)
        band_names = _scrape_BIT_town_site_for_band_names(town_url, driver)
        result.update(band_names)
    bands_names_array = np.array(list(result))
    band_names_df = pd.DataFrame(band_names_array, columns=['band_names'])
    band_names_df.to_csv(file_path_to_save)
    print('DONE')

def _get_list_of_towns(states, filepath = 'uscitiesv1.4'):
    if type(states) == str:
        states = [states]
    df = pd.read_csv(filepath)
    results = df[df.groupby(['county_name'])['population'].transform(max) == df['population']]\
    [df.state_id.isin(states)][['city', 'state_id']].values
    return results

def _convert_townlist_to_urllist(towns):
    result = []
    first_part = 'https://www.bandsintown.com/?location_name='
    seccond_part = '%2C+'
    third_part = '%2C+USA'
    for town in towns:
        result.append(first_part+town[0]+seccond_part+town[1]+third_part)
    return result

def _scrape_BIT_town_site_for_band_names(url, driver):
    '''Scripe One bands in town site for all the bands playing
    in the town. Imputs are a url and a drier that has already
    been started. The driver is pased in so that is does not
    need to start avery time'''
    driver.get(url)
    actions = ActionChains(driver)
    time.sleep(2)
    '''try:
        view_all = driver.find_element_by_css_selector("div.eventList-6f0c6f64")
        print(view_all.text)
        view_all.click()
        #print(view_all.text)
        time.sleep(2)
        new_last_band = driver.find_elements_by_css_selector\
                                        ("div.eventList-b8bed728 h2")[-1]
        last_band = driver.find_elements_by_css_selector(
                                            "div.eventList-b8bed728 h2")[1]
        last_band_text = last_band.text
        new_last_band_text = new_last_band.text
        #print(new_last_band.text)
        print(last_band_text, new_last_band_text)
        while last_band_text != new_last_band_text:
            #last_band = driver.find_elements_by_css_selector("div.eventList-b8bed728 h2")[-1]
            last_band_text = new_last_band_text
            print('SCROLING')
            actions.move_to_element(new_last_band).perform()
            time.sleep(3)
            new_last_band = driver.find_elements_by_css_selector("div.eventList-b8bed728 h2")[-1]
            actions.move_to_element(new_last_band).perform()

            new_last_band_text = new_last_band.text
            print(last_band_text, new_last_band_text)
            #print(new_last_band.text)
    except:
        print('This is a lonely place')'''
    list_of_elements = driver.find_elements_by_css_selector( \
                                      'div.body-cc8a7359 div \
                                      div.upcomingEvents-b6ffb0da \
                                      div div div div div.event-6ea9714d h2 a')
    result = []
    for i, element in enumerate(list_of_elements):
        num_bands = len(list_of_elements)
        bands_bit_website = element.get_attribute('href')
        #print (bands_bit_website)
        band = element.text
        if i % 100 ==1:
            print(band + ' is the ' + str(i) + ' of '\
                  + str(num_bands) + ' on this page')
        result.append(element.text)
    return result

def store_event_data_in_mongo(file_path, mongodb = 'bit_scraping',
                        colection = 'events'):
    band_names = pd.read_csv(file_path)['band_names']
    bad_bands = []
    mc = MongoClient()
    capstone_db = mc[mongodb]
    event_info  = capstone_db[colection]
    for i, band in enumerate(band_names):
        if i%20 == 1:
            print('storing tour', i , 'of', len(band_names))
        tour = _api_events_call(band)
        if tour == band:
            bad_bands.append(band)
        else:
            for j, event in enumerate(tour):
                event_info.update_one({'id':event['id']},
                                     {"$set": event}, upsert=True)
    return bad_bands

def _api_events_call(band):

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

def populate_event_data(list_of_states, mongodb = 'bit_scraping', \
                        colection = 'events'):
    mc = MongoClient()
    capstone_db = mc[mongodb]
    event_info  = capstone_db[colection]
    event_data = pd.DataFrame(list(event_info.find()))


    #pull of the venue info
    #and add it to the dataframe
    #remove the venue column
    venue_data = pd.DataFrame(list(event_data['venue']))
    venue_data.rename(columns = {'name':'venue_name', 'id':'event_id', }, inplace = True )
    df = pd.concat([event_data, venue_data], axis = 1)
    df.drop(labels = 'venue',axis = 1, inplace = True)


    #drop the places where langitude is null
    #because this is how we make venue_id


    df = df[~df.latitude.isnull()]

    '''drop the places not in our states'''

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

def Scrape_BIT_artist_site_for_metadata(artist_id, driver):

    url = 'https://www.bandsintown.com/a/' + str(artist_id)
    driver.get(url)
    actions = ActionChains(driver)
    time.sleep(1)
    try:
        read_more = driver.find_element_by_css_selector('div.artistBio-d6ddfa0a')
        read_more.click()
    except:
        print('Not much info here')
    try:
        genres = driver.find_element_by_css_selector('div.artistBio-172555ec').text
    except:
        genres = None
    try:
        bio = driver.find_element_by_css_selector('div.artistBio-b7fc5660').text
    except:
        bio = None
    try:
        artist_home_town = driver.\
                            find_element_by_css_selector\
                            ('div.artistBio-f8961520\
                            div.artistBio-172555ec').text
    except:
        artist_home_town = None
    return genres, bio, artist_home_town

def _populate_metadata(data):
    driver = Chrome()
    genres = []
    bios = []
    artist_home_towns = []
    result = data.copy()
    artist_list = data['artist_id']
    scrapes = len(artist_list)
    for i, _id in enumerate(artist_list):
        if i%5 == 1:
            print('scrapeing '+ str(i)+ 'of '+ str(scrapes))
        genre, bio, artist_home_town =\
         Scrape_BIT_artist_site_for_metadata(_id, driver)
        if genre == None:
            print(str(_id) + ' has no genre')
        if bio == None:
            print(str(_id)+' has no bio')
        if artist_home_town == None:
            print(str(_id)+' is from everywhere')
        genres.append(genre)
        bios.append(bio)
        artist_home_towns.append(artist_home_town)

    result['artist_genres'] = genres
    result['artist_bios'] = bios
    result['artist_home_town'] = artist_home_towns
    return result

def _make_venue_df(data):
    df_raw1 = data[['venue_name','venue_id','country',\
               'region','city', 'band_genres',\
               'band_bios','latitude', 'longitude']]
    df_raw2 = df_raw1.groupby(['venue_name','venue_id','country','region','city']).\
                                agg({'band_genres':[list], 'band_bios':[list],\
                                'latitude':['mean'], 'longitude':['mean']})
    venue_data = df_raw2.reset_index()
    return venue_data

def populate_artist_data(list_of_states, mongodb = 'bit_scraping', \
                        colection = 'artists'):
    mc = MongoClient()
    capstone_db = mc[mongodb]
    event_info  = capstone_db[colection]
    event_data = pd.DataFrame(list(event_info.find()))


    #pull of the venue info
    #and add it to the dataframe
    #remove the venue column
    venue_data = pd.DataFrame(list(event_data['venue']))
    venue_data.rename(columns = {'name':'venue_name', 'id':'event_id', }, inplace = True )
    df = pd.concat([event_data, venue_data], axis = 1)
    df.drop(labels = 'venue',axis = 1, inplace = True)


    #drop the places where langitude is null
    #because this is how we make venue_id


    df = df[~df.latitude.isnull()]

    '''drop the places not in our states'''

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

def store_artist_data_in_mongo(file_path, mongodb = 'bit_scraping',
                        colection = 'artists'):
    band_names = pd.read_csv(file_path)['band_names']
    bad_bands = []
    mc = MongoClient()
    capstone_db = mc[mongodb]
    artist_info  = capstone_db[colection]
    for i, band in enumerate(band_names):
        if i%200 == 1:
            print('storing band', i , 'of', len(band_names))
        #print(band)
        bandinfo = _api_artist_call(band)
        if bandinfo == band:
            bad_bands.append(band)
        elif 'id' in bandinfo:
            artist_info.update_one({'id':int(bandinfo['id'])},
                                     {"$set": bandinfo}, upsert=True)
    return bad_bands

def _api_artist_call(band):

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
                          "?app_id=2eafc16df6cb4f3db3bb365ca0d91f6e",)

        result = result.json()

        return result
    except:
        return band
