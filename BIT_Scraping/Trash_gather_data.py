
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
import numpy as np
from selenium.common.exceptions import NoSuchElementException


def get_list_of_towns(states, filepath = 'uscitiesv1.4'):
    if type(states) == str:
        states = [states]
    df = pd.read_csv(filepath)
    results = df[df.groupby(['county_name'])['population'].transform(max) == df['population']]\
    [df.state_id.isin(states)][['city', 'state_id']].values
    return results

def scrape_BIT_town_site_for_band_names(url, driver):
    #driver = Chrome()
    driver.get(url)
    actions = ActionChains(driver)
    time.sleep(1)
    try:
        view_all = driver.find_element_by_css_selector("div.eventList-6f0c6f64")
        print(view_all.text)
        view_all.click()
        #print(view_all.text)
        time.sleep(1)
        new_last_band = driver.find_elements_by_css_selector("div.eventList-b8bed728 h2")[-1]
        last_band = driver.find_elements_by_css_selector("div.eventList-b8bed728 h2")[1]
        last_band_text = last_band.text
        new_last_band_text = new_last_band.text
        #print(new_last_band.text)
        while last_band_text != new_last_band_text:
            #last_band = driver.find_elements_by_css_selector("div.eventList-b8bed728 h2")[-1]
            last_band_text = new_last_band_text
            actions.move_to_element(last_band).perform()
            print('SCROLING')
            time.sleep(1)
            new_last_band = driver.find_elements_by_css_selector("div.eventList-b8bed728 h2")[-1]
            new_last_band_text = new_last_band.text
            #print(new_last_band.text)
    except:
        print('This is a lonely place')
    list_of_elements = driver.find_elements_by_css_selector('div.body-cc8a7359 div \
                                      div.upcomingEvents-b6ffb0da \
                                      div div div div div.event-6ea9714d h2 a')
    result = []
    for i, element in enumerate(list_of_elements):
        num_bands = len(list_of_elements)
        bands_bit_website = element.get_attribute('href')
        #print (bands_bit_website)
        thing3 = '%20'.join((element.text).split(' '))
        if i % 100 ==1:
            print(element.text + ' is the ' + str(i) + ' of ' + str(num_bands) + ' on this page')
        result.append(element.text)
    return result


def convert_townlist_to_urllist(towns):
    result = []
    first_part = 'https://www.bandsintown.com/?location_name='
    seccond_part = '%2C+'
    third_part = '%2C+USA'
    for town in towns:
        result.append(first_part+town[0]+seccond_part+town[1]+third_part)
    return result

def STEP_ONE_download_band_names(states, file_path_to_save,
                                         file_to_read_citys = 'uscitiesv1.4.csv',
                                         test = True,
                                         test_iterations = 1):
    driver = Chrome()
    result = set()
    # fist get all the towns
    towns = get_list_of_towns(states, file_to_read_citys)
    town_urls = convert_townlist_to_urllist(towns)
    total_scrapes = (len(towns))
    for i, town_url in enumerate(town_urls):
        if test == True and i > test_iterations:
            break
        print ('Scraping ' + str(i+1) + 'of' + str((total_scrapes)+1))
        print(town_url)
        band_names = scrape_BIT_town_site_for_band_names(town_url, driver)
        result.update(band_names)
    events_array = np.array(list(result))
    event_df = pd.DataFrame(events_array, columns=['band_names'])
    event_df.to_csv(file_path_to_save)
    print('DONE')
