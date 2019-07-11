from flask import Flask, request, make_response
from mongoengine import *
from dotenv import load_dotenv
import json
import requests
import os
import datetime


app = Flask(__name__)
connect('flaskapp')
load_dotenv()

class SongData(EmbeddedDocument):
    saved_songs=ListField(DictField())
    recently_played=ListField(DictField())
    top_songs=ListField(DictField())
    top_artists=ListField(DictField())

class User(Document):
    name= StringField(required=True)
    spotify_id= StringField(required=True)
    access_token=StringField()
    refresh_token=StringField()
    image_links=ListField(DictField())
    friends= ListField(ReferenceField('Friendship'))
    song_data= EmbeddedDocumentField(SongData, default=SongData)


class Friendship(Document):
    status= StringField(required=True, choices=("requested", "pending", "accepted"))
    modified= DateTimeField(default=datetime.datetime.utcnow)
    user= ReferenceField(User)


class Playlist(Document):
    uri= StringField(required=True)
    owners= ListField(ReferenceField(User))

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


@app.route('/login-user',methods=['POST'])
def login_user():
    User.objects().delete() # Clear db so I can test new user creation. Will delete later.
    params = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'), 
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'), 
        'redirect_uri':'playlistfortwo://login/callback', 
        'code': request.form.get('code'),
        'grant_type': 'authorization_code'
        }
    
    result =  requests.post('https://accounts.spotify.com/api/token', data= params)
    if result.status_code != 200 :
        return (result.text, result.status_code)
    token = json.loads(result.text)['access_token']

    user_info = requests.get('https://api.spotify.com/v1/me', 
    headers= {'Authorization': 'Bearer {}'.format(token) }
    )
    if user_info.status_code != 200 :
        return (user_info.text, user_info.status_code)
    user = User.objects(spotify_id=json.loads(user_info.text)['id']).first()

    if not user:
        user = User(
            name=json.loads(user_info.text)['display_name'], 
            spotify_id=json.loads(user_info.text)['id'],
            image_links=json.loads(user_info.text)['images'],
            access_token=json.loads(result.text)['access_token'],
            friends=[],
            refresh_token=json.loads(result.text)['refresh_token']
            )
        user.save()
        user.song_data.saved_songs = get_listening_data(user['spotify_id'], 'saved_songs')
        user.song_data.top_songs= get_listening_data(user['spotify_id'], 'top_songs')
        user.song_data.top_artists= get_listening_data(user['spotify_id'], 'top_artists')
        user.song_data.recently_played = get_listening_data(user['spotify_id'], 'recently_played')
        user.save()

    result = {
            'name' : user.name,
            'spotify_id': user.spotify_id,
            'image_links':user.image_links,
    }

    return (json.dumps(result), 200)
    