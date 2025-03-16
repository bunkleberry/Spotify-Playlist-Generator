import os, random, spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id = os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI'),
    scope = "playlist-modify-private user-library-read playlist-read-private playlist-read-collaborative"
))

def choose_playlist():
    # gets user's playlists
    playlists = sp.current_user_playlists()

    playlist_info = []

    # iterates to print all user playlists + # of songs
    for i, playlist in enumerate(playlists['items']):
        print(f"{i+1}: {playlist['name']} - ({playlist['tracks']['total']} songs)")
        playlist_info.append((playlist))

    return playlist_info

def get_songs(playlist_id):
    tracks = []
    # gets first 100 songs in playlist
    results = sp.playlist_tracks(playlist_id)

    # loops until all songs in playlist are collected (more than 100)
    while results:
        tracks.extend(results['items'])
        results = sp.next(results) if results and results['next'] else None
    
    return tracks

def get_genres(artist_id, artist_genres_cache):
    # checks if an artist needs to be checked for a genre
    if artist_id in artist_genres_cache:
        return artist_genres_cache[artist_id]
    
    # gets all metadata for artist
    artist_info = sp.artist(artist_id)
    # adds all genres for the artist
    artist_genres_cache[artist_id] = artist_info['genres']

    return artist_info['genres']

def common_seeds(playlist_id):
    # stores all songs in playlist
    tracks = get_songs(playlist_id)

    # counts all instances of each genre/artist
    genre_count = Counter()
    artist_count = Counter()

    # avoids duplicate genres for same artist
    artist_genres_cache = {}

    # loops until all metadata for songs genre/artist are collected
    for item in tracks:
        # Check for missing song/artist data
        track = item.get('track')
        if not track:
            continue
        
        # Gets the artist's id and checks for no data (such as self-uploaded songs)
        artists = track.get('artists')
        if not artists or not artists[0].get('id'):
            continue
        
        # gets and stores all instances of artists and their respective ids
        artist_id = artists[0]['id']
        artist_count[artist_id] += 1

        # gets and stores genres
        genres = get_genres(artist_id, artist_genres_cache)
        genre_count.update(genres)

    return genre_count, artist_count

def random_genre_pick(genre_count):
    # separates genres and their respective 
    # number of instances for weighting
    genres = list(genre_count.keys())
    weights = list(genre_count.values())

    # randomly selects 5 genres with weighted values 
    # (for a more preferable playlist for the user)
    rand_genres = random.choices(genres, weights=weights, k=5)

    return rand_genres

def random_artist_pick(artist_count):
    # separates artists and their respective
    # number of instances for weighting
    genres = list(artist_count.keys())
    weights = list(artist_count.values())

    # randomly selects 5 artists with weighted values 
    # (for a more preferable playlist for the user)
    rand_genres = random.choices(genres, weights=weights, k=5)

    return rand_genres

def recommend_songs(rand_genres, rand_artists):
    track_uris = set()

    # iterates to recommend 10 songs per pair of random artist/genre for variety
    for genre, artist in zip(rand_genres, rand_artists):
        # spotify grabs songs from given pair of artist/genre
        recommendations = sp.recommendations(seed_genres=[genre], seed_artists=[artist], limit=10)

        # stores uri for each song from recommendation
        new_songs = [track['uri'] for track in recommendations['tracks']]
        track_uris.update(new_songs)
        
    return list(track_uris)

def create_playlist(name):
    # gets user's id and creates a playlist using a submitted name
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=name, public=False)

    playlist_url = f"https://open.spotify.com/playlist/{playlist['id']}"
    
    return playlist['id'], playlist_url
    
def add_songs(playlist_id, track_uris):
    # adds generated songs to playlist
    sp.playlist_add_items(playlist_id, track_uris)

def main():
    # user selects one of their playlists
    playlists = choose_playlist()
    choice = int(input("Choose the number of the playlist you want to use: ").strip())
    chosen_playlist = playlists[choice-1]
    print(f"You chose playlist {chosen_playlist['name']}")

    # gets and stores dicts for genres and artists
    # and their respective number of instances
    counts = common_seeds(chosen_playlist['id'])
    genre_count = counts[0]
    artist_count = counts[1]

    # randomly selects 5 genres and 5 artists (weighted)
    rand_genres = random_genre_pick(genre_count)
    rand_artists = random_artist_pick(artist_count)

    # stores all recommended songs
    track_uris = recommend_songs(rand_genres, rand_artists)

    # user chooses new playlist name and that playlist 
    # is then generated in their library
    playlist_name = input("Enter the name of your playlist: ")
    playlist_id, playlist_url = create_playlist(playlist_name)
    add_songs(playlist_id, track_uris)
    
    print(f"Your playlist: {playlist_name} has been created!")
    print(f"To access your playlist, check your spotify library or click this link.")
    print(f"{playlist_url}")

if __name__ == '__main__':
    main()