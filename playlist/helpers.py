from dotenv import load_dotenv
import json
import requests
import os
import random
import pandas as pd
from collections import Counter

from .models import User, SongData, Friendship, Playlist

def refresh_token(user_id):
    user = User.objects(spotify_id=user_id).first() 
    params={
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'), 
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'), 
        "grant_type":'refresh_token',
        'refresh_token': user.sp_refresh_token
    }

    response = requests.post("https://accounts.spotify.com/api/token", data=params)

    user.sp_access_token=json.loads(response.text)['access_token']
    user.save()
    return(user.sp_access_token)


def get_listening_data(user_id, data_type):
    user = User.objects(spotify_id=user_id).first()

    endpoints = {
        'saved_songs': 'https://api.spotify.com/v1/me/tracks?offset=0&limit=50',
        'top_songs': 'https://api.spotify.com/v1/me/top/tracks?offset=0&limit=50',
        'top_artists': 'https://api.spotify.com/v1/me/top/artists?offset=0&limit=50',
        'followed_artists': 'https://api.spotify.com/v1/me/following?type=artist&limit=50'
    }
    
    url = endpoints[data_type];
    returned_list = []
    
    while url:
        response = requests.get(url, headers= {
            'Authorization': F'Bearer {user.sp_access_token}'}) 
        if response.status_code == 401:
            refresh_token(user_id)
        elif data_type =='followed_artists':
            returned_list += json.loads(response.text)['artists']['items']
            url = json.loads(response.text)['artists']['next']
        else:
            returned_list += json.loads(response.text)['items']
            url = json.loads(response.text)['next']


    if data_type=='followed_artists' or data_type=='top_artists':
        returned_list = [clean_artist_data(artist) for artist in returned_list]
    elif data_type=='saved_songs' or data_type=='top_songs':
        returned_list = [clean_song_data(track) for track in returned_list]

    return(returned_list)


def clean_artist_data(artist):
    return({
        'name': artist['name'],
        'id': artist['id'],
        'images': artist['images'],
        'genres':artist['genres']
    })


def clean_song_data(track):
    if 'track' in track:
        track = track['track']
    track = {
        'name': track['name'],
        'id': track['id'],
        'artists': [artist['id'] for artist in track['artists']],
        'album':  track['album']['id'],
        'explicit': track['explicit']
        }
    return(track)

def find_common_songs(user1, user2):
    user1_songs = user1.song_data.top_songs + user1.song_data.saved_songs
    user2_songs = user2.song_data.top_songs+ user2.song_data.saved_songs

    user1_songs = set([song['id'] for song in user1_songs])
    user2_songs = set([song['id'] for song in user2_songs])

    return(list(user1_songs.intersection(user2_songs)))

def find_common_artists(user1, user2):
    user1_songs = user1.song_data['top_songs'] + user1.song_data['saved_songs']
    user1_artists_from_songs =  [artist for song in user1_songs for artist in song['artists'] ]
    user1_artists = user1.song_data['top_artists'] + user1.song_data['followed_artists'] 

    user2_songs = user2.song_data['top_songs'] + user2.song_data['saved_songs']
    user2_artists_from_songs =  [artist for song in user2_songs for artist in song['artists'] ]
    user2_artists = user2.song_data['top_artists'] + user2.song_data['followed_artists']

    user1_artists = set([artist['id'] for artist in user1_artists] + user1_artists_from_songs)
    user2_artists = set([artist['id'] for artist in user2_artists] + user2_artists_from_songs)

    return(list(user1_artists & user2_artists))

def get_user_genres(user):
    user_artists = user.song_data['top_artists'] + user.song_data['followed_artists']
    user_genres = [genre for artist in user_artists for genre in artist['genres'] ]
    return (Counter(user_genres))

def find_common_genres(user1, user2, n):
    user1_top_genres = set(dict(get_user_genres(user1).most_common(n)).keys())
    user2_top_genres = set(dict(get_user_genres(user2).most_common(n)).keys())

    return(list(user1_top_genres & user2_top_genres))

def get_user_intersection(user1, user2):
    intersection = {
        'common_songs': find_common_songs(user1, user2),
        'common_artists':find_common_artists(user1, user2),
        'common_genres': find_common_genres(user1, user2, 15)
    }
    return(intersection)    
    
def get_recommendations(intersection):
    token = refresh_token(os.getenv('SPOTIFY_USER_ID'))
    
    songs = [{song_id : 'song'} for song_id in intersection['common_songs']]
    artists = [{artist_id : 'artist'} for artist_id in intersection['common_artists']]
    genres = [{genre : 'genre'} for genre in intersection['common_genres']]

    seeds = random.sample((songs + artists + genres), 5)
    seed_names = get_seed_names(seeds, token)

    seed_songs = ','.join([list(item.keys())[0] for item in seeds if 'song' in item.values()])
    seed_artists = ','.join([list(item.keys())[0] for item in seeds if 'artist' in item.values()])
    seed_genres = ','.join([list(item.keys())[0] for item in seeds if 'genre' in item.values()])

    request_url = F'https://api.spotify.com/v1/recommendations?seed_tracks={seed_songs}&seed_artists={seed_artists}&seed_genres={seed_genres}'

    
    response = requests.get(request_url, 
            headers= {'Authorization': F'Bearer {token}'})

    recommendations = {'seeds': seed_names,
        'recommendations': [clean_song_data(track) for track in json.loads(response.text)['tracks']]
    }

    return(json.dumps(recommendations))

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

def name_from_id(object_id, object_type, token):
        response = requests.get(F'https://api.spotify.com/v1/{object_type}s/{object_id}', headers={'Authorization': F'Bearer {token}' })
    return json.loads(response.text)['name']

def generate_playlist(user1, user2):
    uid = os.getenv('SPOTIFY_USER_ID')
    intersection = get_user_intersection(user1, user2);
    recommendations = get_recommendations(intersection)

    seeds = json.loads(recommendations)['seeds']
    recommendations = json.loads(recommendations)['recommendations']

    token = refresh_token(uid)

    playlist_info = {
        'name': F"{user1.name} and {user2.name}'s Playlist for Two",
        'public':'false',
        'collaborative': 'false',
        'description': F"This playlist was generated by Spotify and the Playlist for Two app based on common songs, artists and genres in {user1.name} and {user2.name}'s music libraries. The seeds used to generate this playlist are {', '.join(seeds)}"
    }

    create_playlist = requests.post(F'https://api.spotify.com/v1/users/{uid}/playlists', headers= {'Authorization': F'Bearer {token}' }, data = json.dumps(playlist_info))

    playlist_id = json.loads(create_playlist.text)['id']

    tracks = ','.join(['spotify:track:{}'.format(track['id']) for track in recommendations])

    add_tracks = requests.post(F'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?uris={tracks}', headers= {'Authorization': 'Bearer {token}' })
  
    return {'seeds': seeds, 'uri':F'spotify:playlist:{playlist_id}'}

def get_features(track):
    features = {
        "danceability": track['danceability'],
        "energy": track['energy'],
        "loudness": track['loudness'],
        "speechiness": track['speechiness'],
        "acousticness": track['acousticness'],
        "instrumentalness": track['instrumentalness'],
        "liveness": track['liveness'],
        "valence": track['valence'],
        "tempo": track['tempo'],
        "id": track['id']
    }
    return(features)

def get_song_analysis_matrix(user):
    token = refresh_token(user_id)
    song_ids = ','.join([song['id'] for song in user.song_data.top_songs])

    response = requests.get(F'https://api.spotify.com/v1/audio-features/?ids={song_ids}',headers={
            'Authorization': F'Bearer {token}'})

    song_analysis_matrix = [features(track) for track in response.body['audio_features']]
    return(song_analysis_matrix)
