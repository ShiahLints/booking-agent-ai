import pymongo
import requests
from bs4 import BeautifulSoup
import time
import json
from selenium.webdriver import Chrome
from pymongo import MongoClient
import pprint

def scrape_calender_row(event):
    
        
    Bands = event.find('h3', {'class': 'calendar-post-title'}).find('a')
    if Bands != None:
        Bands = Bands.get_text(strip=True)
        Bands = Bands.split(sep = ',')
    Date = event.find('p', {'class' : 'calendar-post-date'})
    if Date != None:
        Date = Date.get_text(strip = True)
    Venue = event.find('span', {'class' : 'calendar-post-venue'})
    if Venue != None:
        Venue = Venue.get_text(strip = True)
    Neighborhood = event.find('span', {'class' : 'calendar-post-neighborhood'})
    if Neighborhood != None:
        Neighborhood = Neighborhood.get_text(strip = True)
    Price = event.find('span', {'class' : 'calendar-post-event-price'})
    if Price != None:
        Price = Price.get_text(strip = True)
    eventUrl = event.find('h3', {'class': 'calendar-post-title'}).find('a')['href']
    minAge = event.find('p', {'class' : 'calendar-post-age'})
    if minAge != None:
        minAge = minAge.get_text(strip = True)
    eventSubType = event.find('p', {'class' : 'calendar-post-category'}).find('a')
    if eventSubType != None:
        eventSubType = eventSubType.get_text(strip = True)
    eventType = event.find('span', {'class' : 'label calendar-category'}).find('a')
    if eventType != None:
        eventType = eventType.get_text(strip = True)
    event_id = eventUrl.split(sep = '/')[2]
    
    return ({'_id' : event_id,
            'event_id': event_id,
             'Bands/Title' :Bands, 
             'Date/time' : Date, 
             'Venue': Venue, 
             'Neighborhood' : Neighborhood, 
             'Price' : Price, 
             'eventUrl': eventUrl, 
             'minAge': minAge, 
             'eventSubType': eventSubType,
             'eventType' : eventType})

def scrape_event(website):
    result = {}
    url = website
    page = requests.get(url)
    html = page.content
    soup = BeautifulSoup(page.content, "lxml")
    
    event_id = int(website.split('/')[4])
    
    event_title_bands = soup.find('h1', {'class': 'event-name'}).get_text(strip = True).split(',')
    
    min_age = soup.find ('div', 'event-info pull-left').find('span',{'class': 'event-type'})
    if min_age != None:
        min_age = min_age.get_text(strip = True)

    stared = soup.find('div', {'id': 'event-header'}).find('div', {'class': 'higlights'})
    if stared != None:
        stared = stared.get_text(strip = True)
    
    # price = get from calendar
    
    event_hours = soup.find('div', {'class': 'event-times'}).find('span', {'class': 'list-table-content'})
    if  event_hours != None:
        event_hours = event_hours.get_text(strip=True)
    
    venue_info_page = soup.find('span', {'class': 'event-venue'}).find('a')['href']
    venue_id = int(venue_info_page.split(sep = '/')[2])
    
    #this last scrape might have an error. event description has more then one class
    event_description = soup.find('div', {'id' : 'event-description'}).get_text()

    generas = soup.find('div', {'class': 'event-genres'}).find('span', {'id': 'event-category-bottom'}).find_all('a')
    genera_lst = []
    for genera in generas:
        genera_lst.append(genera.get_text(strip = True))
    generas = genera_lst
    
    return( {'_id' : event_id,
            'event_id': event_id, 
            'event_title_bands':event_title_bands, 
            'min_age':min_age, 
            'stared':stared, 
            'event_hours': event_hours,
            'venue_info_page' : venue_info_page,
            'venue_id':venue_id,
            'eventDescription': Description,
            'generas' : generas
           })

def scrape_venue(website):
    url = website
    page = requests.get(url)
    html = page.content
    soup = BeautifulSoup(page.content, "lxml")

    venue_id = int(website.split(sep = '/')[4])
    
    venue_name = soup.find('h1', {'class' : 'location-name'}).get_text(strip = True)
    
    description = soup.find('div', {'id' : 'location-description'})
    if description != None:
        description = description.get_text()
    
    catagorieSoup = soup.find('span', {'class': 'location-category'})
    if catagorieSoup != None:
        catagorieSoup = catagorieSoup.find_all('a')
        if catagorieSoup != None:
            catagories = []
            for a in catagorieSoup:
                catagories.append(a.get_text())
        catagories = catagories
    
    venue_address = soup.find('span', {'class': 'location-address'})
    if venue_address != None:
        venue_address = venue_address.get_text()
    
    venue_phone = soup.find('div', {'class': 'venue-phone'})
    if venue_phone != None:
        venue_phone = venue_phone.get_text()
    
    venue_website = soup.find('div', {'class': 'venue-website'})
    if venue_website != None:
        venue_website = venue_website.get_text()
    
    location_details = soup.find('div', {'class': 'location-details'})
    # this might fail
    if location_details != None:
        location_features = location_details.find_all('span', {'class': 'list-table-content'})[0].get_text()
        location_scene = location_details.find_all('span', {'class': 'list-table-content'})[1].get_text()
    
    venue_hours = soup.find('div', {'class': 'venue-hours'}).get_text()
    
    return ({'_id' : venue_id,
            'venue_id': venue_id,
            'venue_name': venue_name,
            'description': description,
            'venue_hours': venue_hours,
            'location_catagories': catagories,
            'venue_address': venue_address,
            'venue_phone': venue_phone,
            'venue_website': venue_website,
            'location_features': location_features,
            'location_scene': location_scene})
    
    
    
    

def scrape_calander_pages(start_website, pages):
    url = start_website
    results = []
    print('test')
    for page in range(0, pages):
        print(url)
        page_request = requests.get(url)
        html = page_request.content
        soup = BeautifulSoup(page_request.content, "lxml")
        rows = soup.find_all('div', {'class': 'calendar-post row'})
        for row in rows:
            results.append(scrape_calender_row(row))
        url = soup.find_all('ul', {'class' : 'pager'})[1].find('li',{'class':'next'}).find('a')['href']
        
    return results