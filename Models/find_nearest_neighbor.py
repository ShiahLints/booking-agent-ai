def find_nearest_neighbor_by_artist_genre(artist, bio = True):
    cv = CountVectorizer(stop_words='english', max_features=100)
    artist_with_genres = artists[~artists.genre.isnull()]
    artist_with_genres.iloc[[0]]
    genre_vectors = cv.fit_transform(artist_with_genres.genre)
    c = cv.transform(['latin'])
    c_neighbors = cosine_similarity(genre_vectors, c, dense_output=True)
    a = list((np.argsort(-c_neighbors, axis = 0)[0:10]).reshape(1,-1)[0])