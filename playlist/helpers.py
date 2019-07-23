from dotenv import load_dotenv
from datetime import datetime
import json
import requests
import os
import random
import pandas as pd


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
    if response.status_code !=200:
        response.raise_for_status()

    user.sp_access_token=response.json()['access_token']
    user.save()
    return(user.sp_access_token)
