import pyspark
from pyspark.sql.types import *
from pyspark.ml.tuning import TrainValidationSplit
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
import pandas as pd
import numpy as np


class UV_model(object):
    """docstring for UV_model."""
    def __init__(self, events_data, artists_data, venues_data):

        events_data = pd.read_csv(events_data)
        self.events_data = events_data[events_data.region.isin(['WA','OR','CA'])]
        self.artist_data = pd.read_csv(artists_data)
        venues_data = pd.read_csv(venues_data)
        self.venues_data = venues_data[venues_data.region.isin(['WA','OR','CA'])]
        self.ratings_matrix = self._make_ratings_matrix()
        self.spark = pyspark.sql.SparkSession.builder.getOrCreate()
        self.sc = self.spark.sparkContext
        self.als_model = ALS(userCol='venue_id',
                itemCol='artists_id',
                ratingCol='event_counts',
                nonnegative=True,
                regParam=1,
                rank=10,
                implicitPrefs=True,
                alpha = 40)
        self.als_recomender = None

    def _make_ratings_matrix(self, data):
        matrix_raw = self.data[['artists_id', 'venue_id']].copy()
        matrix_raw['event_counts'] = 1
        matrix_raw = matrix_raw.groupby(['artists_id', 'venue_id'],\
                                as_index = False).count()
        ratings_matrix = pd.DataFrame(matrix_raw)
        ratings_matrix.event_counts += 1
        
        #ratings_matrix.event_counts = np.log(ratings_matrix.event_counts)
        return ratings_matrix

    def fit(self):
        sp_df = self.spark.createDataFrame(self.ratings_matrix)
        self.als_recomender = self.als_model.fit(sp_df)

    def predict_artist_for_city(self, artist, city, state):
        if type(artist) == str:
            band_to_rate = \
                      int(self.artist_data\
                      [self.artist_data.artist_name == artist]\
                      ['artists_id'])
        else:
            band_to_rate = artist

        venues_to_rate = self.venues_data.loc\
        [(self.venues_data['city'] == city) & \
        (self.venues_data['region'] == state)]['venue_id']

        df = pd.DataFrame()
        df['venue_id'] = venues_to_rate
        df['artists_id'] = band_to_rate
        #self.df = df
        rate_this_spark = self.spark.createDataFrame(df)
        predictions_unsorted = self.als_recomender.transform(rate_this_spark)
        predictions_sorted = predictions_unsorted.dropna().sort('prediction',ascending=False)
        panda_predictions = predictions_sorted.toPandas()
        top_predictions = panda_predictions['venue_id'].values[0:10]
        predictied_values = panda_predictions['prediction'].values[0:10]

        return predictied_values, self.venues_data[self.venues_data.venue_id.isin(top_predictions)]

    def predict_artist_for_all_venues(self, artist, n):
        if type(artist) == str:
            band_to_rate = \
                      int(self.artist_data\
                      [self.artist_data.artist_name == artist]\
                      ['artists_id'])
        else:
            band_to_rate = artist
        venues_to_rate = self.venues_data['venue_id']
        df = pd.DataFrame()
        df['venue_id'] = venues_to_rate
        df['artists_id'] = band_to_rate
        #self.df = df
        rate_this_spark = self.spark.createDataFrame(df)
        predictions_unsorted = self.als_recomender.transform(rate_this_spark)
        self.predictions_sorted = predictions_unsorted.dropna().sort('prediction',ascending=False)
        panda_predictions = self.predictions_sorted.toPandas()
        top_predictions = panda_predictions['venue_id'].values[0:n]
        predictied_values = panda_predictions['prediction'].values[0:n]
        result = pd.DataFrame()
        result['venue_name'] = self.venues_data[self.venues_data.venue_id.isin(top_predictions)]['venue_name']
        result['predictions'] = predictied_values

        return result

    def predict_for_artist(self, artist):
        if type(artist) == str:
            band_to_rate = \
                      int(self.artist_data\
                      [self.artist_data.artist_name == artist]\
                      ['artists_id'])
        else:
            band_to_rate = artist

        d = self.events_data[self.events_data.artist_name == artist]
        df = pd.DataFrame()
        df['artists_id'] = d['artists_id']
        df['venue_id'] = d['venue_id']
        rate_this_spark = self.spark.createDataFrame(df)
        predictions = self.als_recomender.transform(rate_this_spark)
        return predictions

    def predict_for_all_artist_all_venues_by_state():
        artist = self.artist_data.artist
