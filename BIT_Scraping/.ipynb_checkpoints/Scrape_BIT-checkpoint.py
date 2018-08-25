
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

def download_band_names(states,file_to_read_citys = 'uscitiesv1.4.csv',
                                         test = False,
                                         test_iterations = 2):
    '''This function gathers artist names  from the bands in town websitself.
    It first calls _git_list_of_towns  to get a list of locations to search.
    It then calls _convert_townlist_to_urllist to get a list of town_urls.
    It then iterates over that list calling _scrape_BIT_town_site_for_band_names.
    It then makes a set of the band names as storye that in a csv file'''
    mc = MongoClient()
    capstone_db = mc['bit_scraping']
    artist_names  = capstone_db['artist_names']
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
        #band_names = _scrape_BIT_town_site_for_band_names(town_url, driver)
        #result.update(band_names)
        _scrape_BIT_town_site_for_band_names(town_url, driver)
    #band_names_array = np.array(list(result))
    #band_names_df = pd.DataFrame(band_names_array, columns=['band_names'])
    #band_names_df.to_csv(file_path_to_save)
    print('DONE')

def _get_list_of_towns(states, filepath = 'uscitiesv1.4'):
    '''This function takes a list of states and returns a list containing
    the city with the highest population in every state'''

    if type(states) == str:
        states = [states]
    df = pd.read_csv(filepath)

    #print (df)
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
    '''Scrape one bands in town site for all the bands playing
    in the town. Imputs are a url and a drier that has already
    been started. The driver is pased in so that is does not
    need to start avery time'''
    mc = MongoClient()
    capstone_db = mc['bit_scraping']
    artist_names  = capstone_db['artist_names']
    driver.get(url)
    actions = ActionChains(driver)
    time.sleep(2)
    try:
        view_all = driver.find_element_by_css_selector("div.eventList-6f0c6f64")
        view_all.click()
        #print(view_all.text)
        time.sleep(2)
        '''new_last_band = driver.find_elements_by_css_selector\
                                        ("div.eventList-b8bed728 h2")[-1]
        last_band = driver.find_elements_by_css_selector(
                                            "div.eventList-b8bed728 h2")[1]
        last_band_text = last_band.text
        new_last_band_text = new_last_band.text
        #print(new_last_band.text)
        while last_band_text != new_last_band_text:
            #last_band = driver.find_elements_by_css_selector("div.eventList-b8bed728 h2")[-1]
            last_band_text = new_last_band_text
            print('SCROLING')
            actions.move_to_element(new_last_band).perform()
            time.sleep(3)
            new_last_band = driver.find_elements_by_css_selector("div.eventList-b8bed728 h2")[-1]
            actions.move_to_element(new_last_band).perform()

            new_last_band_text = new_last_band.text'''
            # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(2)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            #print(new_last_band.text)
    except:
        print('This is a lonely place')
    list_of_elements = driver.find_elements_by_css_selector( \
                                      'div.body-cc8a7359 div \
                                      div.upcomingEvents-b6ffb0da \
                                      div div div div div.event-6ea9714d h2 a')
    result = []
    for i, element in enumerate(list_of_elements):
        #time.sleep(3)
        num_bands = len(list_of_elements)
        bands_bit_website = element.get_attribute('href')
        #print (bands_bit_website)
        band = element.text
        if i % 100 ==1:
            print(band + ' is the ' + str(i) + ' of '\
                  + str(num_bands) + ' on this page')
        #result.append(element.text)
        artist_names.update_one({'name':band},
                             {"$set": {'name': band}}, upsert=True)
    #return result


def store_artist_data_in_mongo():
    driver = Chrome()
    bad_bands = []
    mc = MongoClient()
    capstone_db = mc['bit_scraping']
    artist_info  = capstone_db['artist']
    artist_names  = capstone_db['artist_names']
    band_names = artist_names.distinct('name')
    bands_searched = artist_info.distinct('name')
    bands_to_search = list(set(band_names)-set(bands_searched))

    for i, band in enumerate(bands_to_search):
        if band == None:
            continue
        if i%20 == 1:
            print('storing band', i , 'of', len(bands_to_search))
        #print(band)
        bandinfo = _api_artist_call(band)
        if bandinfo == band:
            print(band+
             ' has no data')
            bad_bands.append(band)
            continue
        elif 'id' in bandinfo:
            artist_info.update_one({'id':bandinfo['id']},
                                     {"$set": bandinfo}, upsert=True)
        band_tour = _api_events_call(band)
        if band_tour == band:
            print(band +' has no tour')
        else:
            artist_info.update_one({'id':bandinfo['id']},
                                    {'$set':{'tour':band_tour}}, upsert = True)
        genre, bio, home_town = _scrape_BIT_artist_site_for_metadata(bandinfo['id'], driver)
        #print(genre, bio, home_town)
        artist_info.update_one({'id':bandinfo['id']},
                                {'$set':{'genre':genre, 'bio': bio,
                                'home_town': home_town}}, upsert = True)

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
        if result == '':
            return band
        if 'error' in result:
            return band
        return result
    except:
        return band

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
                          "/events?app_id=2eafc16df6cb4f3db3bb365ca0d91f6e")

        result = result.json()
        for event in result:
            event['band_name'] = band

        return result
    except:
        return band

def _scrape_BIT_artist_site_for_metadata(artist_id, driver):

    url = "https://www.bandsintown.com/a/" + str(artist_id)
    driver.get(url)
    actions = ActionChains(driver)
    time.sleep(1)
    try:
        read_more = driver.find_element_by_css_selector('div.artistBio-d6ddfa0a')
        read_more.click()
    except:
        print('')

    try:
        genres = driver.find_element_by_css_selector('div.artistBio-172555ec').text
    except:
        print (artist_id + 'has no genre')
        genres = None
    try:
        bio = driver.find_element_by_css_selector('div.artistBio-b7fc5660').text
    except:
        bio = None
        print (artist_id + 'has no bio')
    try:
        artist_home_town = driver.\
                            find_element_by_css_selector\
                            ('div.artistBio-f8961520\
                            div.artistBio-172555ec').text
    except:
        print (artist_id + 'has no home town')
        artist_home_town = None
    return genres, bio, artist_home_town
