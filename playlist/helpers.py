from dotenv import load_dotenv
import json
import requests
import os
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
            'Authorization': 'Bearer {}'.format(user.sp_access_token) 
            }
        ) 
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

def find_common_albums(user1, user2):
    user1_songs = user1.song_data.top_songs + user1.song_data.saved_songs
    user2_songs = user2.song_data.top_songs+ user2.song_data.saved_songs

    user1_albums = set([song['album'] for song in user1_songs])
    user2_albums = set([song['album'] for song in user2_songs])

    return(list(user1_albums & user2_albums))

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
        'common_albums':find_common_albums(user1, user2),
        'common_artists':find_common_artists(user1, user2),
        'common_genres': find_common_genres(user1, user2, 15)
    }
    return(intersection)
    
    
def get_song_analysis_matrix(user):
    song_ids = ','.join([song['id'] for song in user.song_data.top_songs])

    response = requests.get(F'https://api.spotify.com/v1/audio-features/?ids={song_ids}',{
            'Authorization': 'Bearer {}'.format(user.sp_access_token) 
            })

    song_analysis_matrix = [features(track) for track in response.body['audio_features']]
    return(song_analysis_matrix)


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

