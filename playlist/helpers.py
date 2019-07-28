import json
import os
import requests


from .models import User


def refresh_token(user_id):
    user = User.objects(spotify_id=user_id).first()
    params = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
        "grant_type": 'refresh_token',
        'refresh_token': user.sp_refresh_token
    }

    response = requests.post(
        "https://accounts.spotify.com/api/token", data=params)
    if response.status_code != 200:
        response.raise_for_status()

    user.sp_access_token = response.json()['access_token']
    user.save()

    return user.sp_access_token


def find_user_info(user_id):
    user = User.objects(spotify_id=user_id).first()
    if user:
        response = {
            'name': user.name,
            'spotify_id': user.spotify_id,
            'image_links': user.image_links,
        }

        return (json.dumps(response), 200)
    else:
        return ({'error': 'Could not locate user info'}, 404)
