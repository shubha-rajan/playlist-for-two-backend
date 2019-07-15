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
        'followed_artists': 'https://api.spotify.com/v1/me/following?type=artist&limit=50'
    }
    
    url = endpoints[data_type];
    returned_list = []
    
    while url:
        response = requests.get(url, headers= {
            'Authorization': 'Bearer {}'.format(user.access_token) 
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

