import pandas as pd
import cosinrecomender

#master_venues = pd.read_pickle('data/master_venues_df.p')
master_artists = pd.read_pickle('data/master_artists_df.p')
citys = pd.read_csv('data/uscitiesv1.4.csv').city.values
#top_n = number_of_recomendations
recomender = cosinrecomender.Recomender()
def recomend():
    #user_type = input('''Are you a fan looking for a show \n or a artist looking for a venue.\nPlease enter F or A''')
    state_id = input('''What State do you want to search in?
Please enter WA, CA or OR  ''')
    city = input('''What city do you want to center you search on'''+
    ''' Please make the first word a cap ''')
    radius = input('''What is the radius in miles you would like to search? ''')
    radius = int(radius)
    artist_name = input('Please enter the name of your band ')
    artist = (master_artists[master_artists.artist_name == artist_name])
    artist_bio = artist.artist_bio.values[0]
    artist_genre = artist.artist_genre.values[0]
    result = recomender.get_best_fit_for_artist(city, state_id, radius,\
                                artist_genre = artist_genre, artist_bio = artist_bio)
    return result
