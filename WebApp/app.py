from flask import Flask, render_template, request, jsonify
from model import recomend
import cosinrecomender
import pandas as pd
app = Flask(__name__)

artists = pd.read_pickle('../data/master_artists_df.p')
artist_names = sorted(list(artists['artist_name'].values))

@app.route('/', methods=['GET'])
def index():
    return render_template('recommender.html', artist_names = artist_names)


@app.route('/search/', methods=['POST'])
def solve():
    user_data = request.json
    artist_name = user_data['artist_name']
    city = user_data['city']
    state = user_data['state']
    radius = int(user_data['radius'])
    artist_genre1 = user_data['artist_genre']
    results = recomend(artist_name, state, city, radius, artist_genre1)
    return jsonify(results)



if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
