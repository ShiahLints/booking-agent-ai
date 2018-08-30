import pandas as pd
import numpy as np
import find_nearest_venues as fnv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

master_venues = pd.read_pickle('data/master_venues_df.p')


class Recomender(object):
    """Cosine_similarity recomender"""
    def __init__(self, number_of_recomendations = 10):
        self.master_venues = pd.read_pickle('data/master_venues_df.p')
        self.master_artists = pd.read_pickle('data/master_artists_df.p')
        self.vf = fnv.Venue_Finder()
        self.top_n = number_of_recomendations

    def get_best_fit_for_artist(self, city, state, milage,\
                                artist_genre = None, artist_bio = None):
        venues = self.vf.get_nearest_venues_by_city(city, state, milage)
        if artist_bio != None:
            bio_recs = self.find_nearest_neighbor_by_bio(artist_genre, venues)
            return bio_recs.head(self.top_n)
        if artist_genre != None:
            genre_recs = self.find_nearest_neighbor_by_genre(artist_genre, venues, milage)
            return genre_recs.head(self.top_n)
        bio_input = input('''This Artist does not have enough input please wright a short blurb describing them''')
        return self.find_nearest_neighbor_by_genre(bio_input, venues).head(self.top_n)

    def find_nearest_neighbor_by_bio(self, artist_bio, venues):
        cv = CountVectorizer(stop_words='english', max_features=1000)
        venues_with_doc = venues[~venues.venue_bio.isnull()]
        venue_vectors = cv.fit_transform(venues_with_doc.venue_bio)
        artist_vector = cv.transform([artist_bio])
        artist_neighbors = cosine_similarity(venue_vectors, artist_vector, dense_output=True)
        a = list((np.argsort(-artist_neighbors, axis = 0)).reshape(1,-1)[0])
        neighbors = venues_with_doc.iloc[a,:]
        return neighbors

    def find_nearest_neighbor_by_genre(self, artist_genre, venues):
        cv = CountVectorizer(stop_words='english', max_features=300)
        venues_with_doc = venues[~venues.venue_genre.isnull()]
        venue_vectors = cv.fit_transform(venues_with_doc.venue_genre)
        artist_vector = cv.transform([artist_genre])
        artist_neighbors = cosine_similarity(venue_vectors, artist_vector, dense_output=True)
        a = list((np.argsort(-artist_neighbors, axis = 0)[0:10]).reshape(1,-1)[0])
        neighbors = venues_with_doc.iloc[a,:]
        return neighbors
