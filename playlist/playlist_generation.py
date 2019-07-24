from datetime import datetime
import json
import requests
import os
import random

from .helpers import refresh_token
from .intersection import get_user_intersection
from .listening_data import clean_song_data


def clean_playlist_track_data(track):
    if 'track' in track:
        track = track['track']
    return (
        {
            'name': track['name'],
            'id': track['id'],
            'artists': [artist['name'] for artist in track['artists']]
        }
    )
    
def get_seeds(intersection):
    songs = [{song['id'] : 'song'} for song in intersection['common_songs']]
    artists = [{artist['id'] : 'artist'} for artist in intersection['common_artists']]
    genres = [{genre : 'genre'} for genre in intersection['common_genres']]

    if len(songs + artists + genres) > 5:
        seeds = random.sample((songs + artists + genres), 5)
    else:
        seeds = songs + artists + genres
    
    return seeds

def get_recommendations(intersection):
    token = refresh_token(os.getenv('SPOTIFY_USER_ID'))
    
    seeds = get_seeds(intersection)

    seed_songs = ','.join([list(item.keys())[0] for item in seeds if 'song' in item.values()])
    seed_artists = ','.join([list(item.keys())[0] for item in seeds if 'artist' in item.values()])
    seed_genres = ','.join([list(item.keys())[0] for item in seeds if 'genre' in item.values()])

    request_url = F'https://api.spotify.com/v1/recommendations?seed_tracks={seed_songs}&seed_artists={seed_artists}&seed_genres={seed_genres}'

    seed_names = get_seed_names(seeds, token)

    response = requests.get(request_url, 
            headers= {'Authorization': F'Bearer {token}'})
    if response.status_code != 200:
        response.raise_for_status
    
    recommendations = {'seeds': seed_names,
        'recommendations': [clean_song_data(track) for track in response.json()['tracks']]
    }

    return(recommendations)

def get_seed_names(seeds, token):
    seed_names = []
    
    for seed in seeds:
        if 'song' in seed.values():
            song_id = list(seed.keys())[0] 
            song_name = name_from_id(song_id, 'track', token)
            seed_names.append(F'{song_name} (song)')
        elif 'artist' in seed.values():
            artist_id = list(seed.keys())[0] 
            artist_name = name_from_id(artist_id, 'artist', token)
            seed_names.append(F'{artist_name} (artist)')
        else:
            genre = list(seed.keys())[0] 
            seed_names.append(F'{genre} (genre)')
    return seed_names  

def name_from_id(object_id, object_type, token=None):
    if not token:
        token = refresh_token(os.getenv('SPOTIFY_USER_ID'))
    response = requests.get(F'https://api.spotify.com/v1/{object_type}s/{object_id}', headers={'Authorization': F'Bearer {token}' })
    if response.status_code != 200:
        response.raise_for_status()
    else:
        return response.json()['name']

def generate_playlist(user1, user2):
    uid = os.getenv('SPOTIFY_USER_ID')
    intersection = get_user_intersection(user1, user2);
    recommendations = get_recommendations(intersection)

    seeds = recommendations['seeds']
    recommendations = recommendations['recommendations']

    token = refresh_token(uid)

    dt = datetime.now().strftime("%B %d, %Y %I:%M%p")

    playlist_info = {
        'name': F"{dt} - {user1.name} and {user2.name}'s Playlist for Two",
        'public':'false',
        'collaborative': 'false',
        'description': F"This playlist was generated by Spotify and the Playlist for Two app based on common songs, artists and genres in {user1.name} and {user2.name}'s music libraries. The seeds used to generate this playlist are {', '.join(seeds)}"
    }

    create_playlist = requests.post(F'https://api.spotify.com/v1/users/{uid}/playlists', headers= {'Authorization': F'Bearer {token}' }, data = json.dumps(playlist_info))

    if create_playlist.status_code != 200:
        create_playlist.raise_for_status

    playlist_id = create_playlist.json()['id']

    tracks = ','.join(['spotify:track:{}'.format(track['id']) for track in recommendations])

    add_tracks = requests.post(F'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?uris={tracks}', headers= {'Authorization': F'Bearer {token}'})

    if add_tracks.status_code == 200 or add_tracks.status_code == 201:
        return {'seeds': seeds, 'uri':F'spotify:playlist:{playlist_id}' , 'description': playlist_info}
    else:
        add_tracks.raise_for_status()

def get_tracks_from_id(playlist_id):
    token = refresh_token(os.getenv('SPOTIFY_USER_ID'))
    response = requests.get(F'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers= {'Authorization': F'Bearer {token}'})

    if (response.status_code == 200):
        tracks = response.json()['items']
        tracks = [clean_playlist_track_data(track) for track in tracks]
        return tracks
    else:
        response.raise_for_status()

    