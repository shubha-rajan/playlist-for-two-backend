from dotenv import load_dotenv
import json
import requests
import os

from .models import User, SongData, Friendship, Playlist

def refresh_token(user_id):
    user = User.objects(spotify_id=user_id).first() 
    params={
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'), 
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'), 
        "grant_type":'refresh_token',
        'refresh_token': user.refresh_token
    }

    response = requests.post("https://accounts.spotify.com/api/token", data=params)

    user.access_token=json.loads(response.text)['access_token']
    user.save()
    return(user.access_token)


def get_listening_data(user_id, data_type):
    user = User.objects(spotify_id=user_id).first()

    endpoints = {
        'saved_songs': 'https://api.spotify.com/v1/me/tracks?offset=0&limit=50',
        'top_songs': 'https://api.spotify.com/v1/me/top/tracks?offset=0&limit=50',
        'top_artists': 'https://api.spotify.com/v1/me/top/artists?offset=0&limit=50',
        'recently_played': 'https://api.spotify.com/v1/me/player/recently-played?offset=0&limit=50'
    }
    
    url = endpoints[data_type];
    track_list = []
    
    while url:
        response = requests.get(url, headers= {
            'Authorization': 'Bearer {}'.format(user.access_token) 
            }
        ) 
        if response.status_code == 401:
            refresh_token(user_id)
        else:
            track_list += json.loads(response.text)['items']
            url = json.loads(response.text)['next']
    
    return(track_list)


def all_listening_data(user): 
        user.song_data.saved_songs = get_listening_data(user['spotify_id'], 'saved_songs')
        user.song_data.top_songs= get_listening_data(user['spotify_id'], 'top_songs')
        user.song_data.top_artists= get_listening_data(user['spotify_id'], 'top_artists')
        user.song_data.recently_played = get_listening_data(user['spotify_id'], 'recently_played')
        user.save()