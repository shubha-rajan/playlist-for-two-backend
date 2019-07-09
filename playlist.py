from flask import Flask, request, make_response
from mongoengine import *
from dotenv import load_dotenv
import json
import requests
import os
import datetime
import spotipy as sp

app = Flask(__name__)
connect('flaskapp')
load_dotenv()

class SongData(EmbeddedDocument):
    songs=ListField(StringField())
    artists=DictField()
    albums=DictField()
    genres=DictField()

class User(Document):
    name= StringField(required=True)
    spotify_id= StringField(required=True)
    access_token=StringField()
    refresh_token=StringField()
    image_links=ListField(DictField())
    friends= ListField(ReferenceField('Friendship'))
    song_data= EmbeddedDocumentField(SongData)


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

    user['access_token']=json.loads(response.text)['access_token']
    user.save()
    return(user.access_token)

def get_song_list(user_id):
    user = User.objects(spotify_id=user_id).first()
    url = 'https://api.spotify.com/v1/me/tracks?offset=0&limit=50'
    track_list = []
    
    while url:
        response = requests.get(url, headers= {
            'Authorization': 'Bearer {}'.format(user['access_token']) 
            }
        ) 
        
        if response.status_code == 401:
            refresh_token(user_id)
        else:
            track_list += json.loads(response.text)['items']
            url = json.loads(response.text)['next']
    return(track_list)


@app.route('/')
def index():
    return 'It\'s Flask!'

@app.route('/login-user',methods=['POST'])
def login_user():
    params = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'), 
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'), 
        'redirect_uri':'playlistfortwo://login/callback', 
        'code': request.form.get('code'),
        'grant_type': 'authorization_code'
        }
    
    result =  requests.post('https://accounts.spotify.com/api/token', data= params)
    token = json.loads(result.text)['access_token']

    user_info = requests.get('https://api.spotify.com/v1/me', 
    headers= {'Authorization': 'Bearer {}'.format(token) }
    )
    user = User.objects(spotify_id=json.loads(user_info.text)['id']).first()

    if not user:
        user = User(
            name=json.loads(user_info.text)['display_name'], 
            spotify_id=json.loads(user_info.text)['id'],
            image_links=json.loads(user_info.text)['images'],
            access_token=json.loads(result.text)['access_token'],
            refresh_token=json.loads(result.text)['refresh_token'])
        user.save()

    get_song_list(user['spotify_id'])
    return (user.to_json(), user_info.status_code)
    