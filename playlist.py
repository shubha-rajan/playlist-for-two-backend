from flask import Flask, request, make_response

from dotenv import load_dotenv
import json
import requests
import os

import mongoengine

from .models import User, SongData, Friendship, Playlist
from .helpers import refresh_token, all_listening_data, get_listening_data

app = Flask(__name__)
mongoengine.connect('flaskapp')
load_dotenv()


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
        all_listening_data(user)
    

    result = {
            'name' : user.name,
            'spotify_id': user.spotify_id,
            'image_links':user.image_links,
    }

    return (json.dumps(result), 200)
    