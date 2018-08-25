from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def remove_stopword(text):
    stopwords = ['the', 'with', 'guest']
    return ' '.join(word for word in text.split() if word and word not in stopwords)
    

def pre_process_venue_names(events):
    events['vn_original'] = events['venue_name'].copy()
    events['venue_name'] = events['venue_name'].str.lower()
    events['venue_name'] = events['venue_name'].str.replace('[^\w\s]','').str.strip()
    stopwords = ['the', 'with', 'guest']
    events['venue_name'] = events['venue_name'].apply(remove_stopword)
    return events
    

def convert_city_venue_name(dataset, state, city, threshold= 86):
    state_events = dataset[dataset['region'] == state]
    city_events = state_events[state_events['city'] == city]
    venues = set(city_events['venue_name'])
    conversion_dct = {}
    for i, venue in enumerate(venues):
        if i%40 == 0:
            print (i ,' of ',len(venues))
        try:
            alt_name, prob = process.extract(venue, venues, limit = 2)[1]
        except:
            continue
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
            dataset.at[i, 'venue_name'] = conversion_dct[venue_name]

    return (dataset)

# now run the code from generate_tables to take this data set
# and make a vuneus table
# save the venues table
# after the venues table is made run the code 
# add merge the venue_ids with the venue names in this data set 
# and save this data set