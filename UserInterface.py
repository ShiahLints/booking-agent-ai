import find_nearest_venues
import pandas as pd

events = pd.read_pickle('data/master_events_df.p'))
venues = pd.read_pickle('/data/master_venues.p')
artists = pd.read_pickle('/data/master_artists.p')


def find_nearest_neighbor_by_doc(artist_doc, venues, venue_column, features):
    cv = CountVectorizer(stop_words='english', max_features=features)
    venues_with_doc = venues[~venues[venue_column].isnull()]
    venue_vectors = cv.fit_transform(venues_with_doc[venue_column])
    artist_vector = cv.transform([artist_doc])
    artist_neighbors = cosine_similarity(venue_vectors, artist_vector, dense_output=True)
    a = list(np.argsort(-artist_neighbors, axis = 0).reshape(1,-1)[0])
    neighbors = venues_with_doc.iloc[a,:]
    return list(neighbors)
