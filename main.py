from flask import Flask, request, make_response
from dotenv import load_dotenv
from functools import wraps

import json
import requests
import os
import jwt
from datetime import datetime

import mongoengine

from playlist.models import User, SongData, Friendship, Playlist
from playlist.helpers import refresh_token
from playlist.listening_data import  load_user_data, get_user_genres
from playlist.friend_requests import send_friend_request, accept_friend_request, get_friend_list
from playlist.intersection import get_user_intersection 
from playlist.playlist_generation import name_from_id, get_recommendations, generate_playlist, get_tracks_from_id

app = Flask(__name__)
mongoengine.connect('flaskapp', host=os.getenv('MONGODB_URI'))
load_dotenv()

def authorize_user(func):
    @wraps(func)
    def function_with_authorization(*args, **kws):
        encoded_jwt = request.headers.get("authorization")
        try:
            decoded = jwt.decode(encoded_jwt, os.getenv('JWT_SECRET'), algorithm='HS256')
        except:
            return ({"error": "You are not authorized to perform that action."}, 401)
        else:
            return func(*args, **kws)
    return function_with_authorization

def confirm_user_identity(func):
    @wraps(func)
    def function_with_identification(*args, **kws):
        user_id = request.args.get("user_id")
        if not user_id:
            user_id = request.form.get("user_id")
        user = User.objects(spotify_id=user_id).first() 

        encoded_jwt = request.headers.get("authorization")
        decoded = jwt.decode(encoded_jwt, os.getenv('JWT_SECRET'), algorithm='HS256')

        if not (user.spotify_id==decoded['id']):
            return ({"error": "You are not authorized to perform that action."}, 401)
        else:
            return func(*args, **kws)
    return function_with_identification
    


@app.route('/',methods=['GET'])
def hello_flask():
    return ("It's working!")

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
            sp_access_token =json.loads(result.text)['access_token'],
            friends=[],
            playlists=[],
            sp_refresh_token=json.loads(result.text)['refresh_token']
            )
        user.save()
    else:
        user.sp_access_token =json.loads(result.text)['access_token']
        user.sp_refresh_token=json.loads(result.text)['refresh_token']
        user.save()

    encoded_jwt =jwt.encode({'id': user.spotify_id, 'iat': datetime.utcnow()}, os.getenv('JWT_SECRET'), algorithm='HS256')

        
    return (encoded_jwt, 200)

@app.route('/me',methods=['GET'])
@authorize_user
def get_logged_in_user_info():
    encoded_jwt = request.headers.get("authorization")
    decoded = jwt.decode(encoded_jwt, os.getenv('JWT_SECRET'), algorithm='HS256')

    user = User.objects(spotify_id=decoded['id']).first() 
    if user:
        response = {
                'name' : user.name,
                'spotify_id': user.spotify_id,
                'image_links':user.image_links,
        }

        return (json.dumps(response), 200)
    else:
        return ({'error': 'Could not locate user info'}, 404)

@app.route('/listening-history',methods=['GET'])
@authorize_user
@confirm_user_identity
def get_listening_history():    
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first() 

    if not user:
        return ({'error':F'could not find user with id {user_id}'}, 404)

    try:
        load_user_data(user)
    except requests.exceptions.HTTPError as http_err:
            print(http_err)
    except requests.exceptions.ConnectionError as conn_err:
            print(conn_err)
    except requests.exceptions.Timeout as timeout_err:
            print(timeout_err)
    except requests.exceptions.RequestException as err:
            print(err)
    else:
        return (user.song_data.to_json(), 200)

@app.route('/request-friend',methods=['POST'])
@authorize_user
@confirm_user_identity
def request_friend():
    user_id = request.form.get("user_id")
    friend_id = request.form.get("friend_id")

    user = User.objects(spotify_id=user_id).first() 
    requested = User.objects(spotify_id=friend_id).first()

    if not user:
        return ({'error':F'could not find user with id {user_id}'}, 404)
    elif not requested:
        return ({'error':F'could not find user with id {friend_id}'}, 404)

    if send_friend_request(user, requested):
        return (F"Successfully sent a friend request to user #{friend_id}.", 200)
    else:
        return(F'Could not send friend request to #{friend_id}.', 400)

@app.route('/accept-friend',methods=['POST'])
@authorize_user
@confirm_user_identity
def accept_friend():
    user_id = request.form.get("user_id")
    friend_id = request.form.get("friend_id")

    if accept_friend_request(user_id, friend_id):
        return (F"Successfully added user #{friend_id} as a friend.", 200)
    else:
        return(F'Could not add user #{friend_id} as a friend.', 400)

@app.route('/friends',methods=['GET'])
@authorize_user
@confirm_user_identity
def get_friends():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first() 

    if not user:
        return ({'error':F'could not find user with id {user_id}'}, 404)

    try:
        response = get_friend_list(user)
    except:
        return ({"error":"There was a problem retrieving information from the database"}, 400)
    else:
        return(json.dumps(response), 200)

@app.route('/users',methods=['GET'])
@authorize_user
def all_users():
    encoded_jwt = request.headers.get("authorization")
    decoded = jwt.decode(encoded_jwt, os.getenv('JWT_SECRET'), algorithm='HS256')

    user_uid = decoded['id']
    app_uid=os.getenv('SPOTIFY_USER_ID')

    try:
        response = User.objects(spotify_id__nin=[user_uid, app_uid]).only('name', 'spotify_id')
    except:
        return ({"error":"There was a problem retrieving information from the database"}, 400)
    else:
        return(response.to_json(), 200)

@app.route('/genres',methods=['GET'])
@authorize_user
def user_genres():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first() 

    if not user:
        return ({'error':F'could not find user with id {user_id}'}, 404)

    try:
        genres = get_user_genres(user)
    except:
        return ({"error":"There was a problem retrieving information from the database"}, 400)
    else:
        return(json.dumps(dict(genres.most_common(20))), 200)

@app.route('/intersection', methods=['GET'])
@authorize_user
def find_intersection():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first() 
    friend_id = request.args.get("friend_id")
    friend = User.objects(spotify_id=friend_id).first() 

    if not user:
        return ({'error':F'could not find user with id {user_id}'}, 404)
    elif not friend:
        return ({'error':F'could not find user with id {friend_id}'}, 404)
    
    try:  
        load_user_data(user)
        load_user_data(friend)
    except requests.exceptions.HTTPError as http_err:
        print(http_err)
    except requests.exceptions.ConnectionError as conn_err:
        print(conn_err)
    except requests.exceptions.Timeout as timeout_err:
        print(timeout_err)
    except requests.exceptions.RequestException as err:
        print(err)
    else:
        intersection = get_user_intersection(user, friend)
        intersection = {
            "common_songs": [json.dumps({'name':name_from_id(song_id, 'track'), 'id':song_id}) for song_id in intersection['common_songs']],
            "common_artists": [json.dumps({'name':name_from_id(artist_id, 'artist'), 'id':artist_id}) for artist_id in intersection['common_artists']],
            'common_genres': intersection['common_genres']
        }
        return(json.dumps(intersection), 200)

@app.route('/recommendations', methods=['GET'])
@authorize_user
@confirm_user_identity
def find_reccomendations():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first() 
    friend_id = request.args.get("friend_id")
    friend = User.objects(spotify_id=friend_id).first() 
    
    if not user:
        return ({'error':F'could not find user with id {user_id}'}, 404)
    elif not friend:
        return ({'error':F'could not find user with id {friend_id}'}, 404)

    intersection = get_user_intersection(user, friend)

    result = get_recommendations(intersection)
    return(result)

@app.route('/new-playlist', methods=['POST'])
@authorize_user
@confirm_user_identity
def create_new_playlist():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first() 
    friend_id = request.args.get("friend_id")
    friend = User.objects(spotify_id=friend_id).first()

    if not user:
        return ({'error':F'could not find user with id {user_id}'}, 404)
    elif not friend:
        return ({'error':F'could not find user with id {friend_id}'}, 404)
    
    try:
        playlist = generate_playlist(user, friend)
    except requests.exceptions.HTTPError as http_err:
        print(http_err)
    except requests.exceptions.ConnectionError as conn_err:
        print(conn_err)
    except requests.exceptions.Timeout as timeout_err:
        print(timeout_err)
    except requests.exceptions.RequestException as err:
        print(err)
    else:
        new_playlist = Playlist(
            uri= playlist['uri'],
            description=playlist['description'],
            seeds=playlist['seeds'],
            owners=[user_id, friend_id]
        )
        user.playlists.append(new_playlist)
        friend.playlists.append(new_playlist)
        user.save()
        friend.save()
        if new_playlist in user.playlists and new_playlist in friend.playlists:
            return (json.dumps(playlist))
        else:
            return (json.dumps({"error": "failed to save playlist"}), 400)

@app.route('/playlists', methods=['GET'])
@authorize_user
@confirm_user_identity
def get_playlists():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first() 
    friend_id = request.args.get("friend_id")

    if not user:
        return ({'error':F'could not find user with id {user_id}'}, 404)
    
    shared_playlists = [json.loads(playlist.to_json()) for playlist in user.playlists if friend_id in playlist.owners]

    return (json.dumps(shared_playlists), 200)

@app.route('/playlist', methods=['GET']) 
@authorize_user 
def get_playlist_tracks():
        playlist_id= request.args.get("playlist_id")

        try:
            track_list = get_tracks_from_id(playlist_id)
        except requests.exceptions.HTTPError as http_err:
            print(http_err)
        except requests.exceptions.ConnectionError as conn_err:
            print(conn_err)
        except requests.exceptions.Timeout as timeout_err:
            print(timeout_err)
        except requests.exceptions.RequestException as err:
            print(err)
        else:
            return (json.dumps(track_list), 200)

