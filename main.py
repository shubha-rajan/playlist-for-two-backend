from functools import wraps
from datetime import datetime, timedelta
import os
import json

from flask import Flask, request
import requests
from dotenv import load_dotenv
import jwt
import mongoengine

from playlist.models import User, Playlist
from playlist.helpers import find_user_info
from playlist.listening_data import load_user_data, get_user_genres
from playlist.friend_requests import (send_friend_request, accept_friend_request,
                                      get_friend_list, remove_friend_from_database,
                                      )
from playlist.intersection import get_user_intersection
from playlist.recommendations import get_rec_from_intersection
from playlist.playlists import (generate_playlist, get_tracks_from_id,
                                set_playlist_details, delete_from_user_playlists)

app = Flask(__name__)
mongoengine.connect('flaskapp', host=os.getenv('MONGODB_URI'))
load_dotenv()


def authorize_user(func):
    @wraps(func)
    def function_with_authorization(*args, **kws):
        encoded_jwt = request.headers.get("authorization")
        try:
            jwt.decode(encoded_jwt, os.getenv(
                'JWT_SECRET'), algorithm='HS256', audience="client")
        except (jwt.InvalidTokenError, jwt.InvalidAudienceError, jwt.InvalidIssuedAtError):
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
        if not user:
            return({"error": "Your token could not be verified"}, 401)

        encoded_jwt = request.headers.get("authorization")
        decoded = jwt.decode(encoded_jwt, os.getenv(
            'JWT_SECRET'), algorithm='HS256', audience="client")

        if not user.spotify_id == decoded['id']:
            return ({"error": "You are not authorized to perform that action."}, 401)
        else:
            return func(*args, **kws)
    return function_with_identification


def check_for_request_errors(func):
    @wraps(func)
    def request_error_handling(*args, **kws):
        try:
            result = func(*args, **kws)
        except requests.exceptions.HTTPError as http_err:
            return ({"error": F"There was a problem with your request: {http_err}"}, 400)
        except requests.exceptions.ConnectionError as conn_err:
            return ({"error": F"There was a problem with your request: {conn_err}"}, 503)
        except requests.exceptions.Timeout as timeout_err:
            return ({"error": F"There was a problem with your request: {timeout_err}"}, 408)
        except requests.exceptions.RequestException as err:
            return ({"error": F"There was a problem with your request: {err}"}, 400)
        else:
            return result
    return request_error_handling


def check_for_db_errors(func):
    @wraps(func)
    def db_error_handling(*args, **kws):
        try:
            result = func(*args, **kws)

        except mongoengine.errors.NotUniqueError as uniq_err:
            return (
                {"error": F"There was a problem saving to the database: {uniq_err}"}, 400)
        except mongoengine.errors.ValidationError as val_err:
            return (
                {"error": F"There was a problem saving to the database: {val_err}"}, 400)
        except mongoengine.errors.FieldDoesNotExist as fdne_err:
            return (
                {"error": F"There was a problem reading/writing to the database: {fdne_err}"}, 400)
        except mongoengine.errors.DoesNotExist as dne_err:
            return (
                {"error": F"There was a problem reading from the database: {dne_err}"}, 404)
        except mongoengine.errors.MultipleObjectsReturned as mult_err:
            return (
                {"error": F"There was a problem reading from the database {mult_err}"}, 400)
        else:
            return result
    return db_error_handling


@app.route('/', methods=['GET'])
def hello_flask():
    return "It's working!"


@app.route('/coffee', methods=['GET'])
def im_a_teapot():
    return ({"error": "I can't brew coffee because I'm a teapot!"}, 418)


@check_for_db_errors
@app.route('/login-user', methods=['POST'])
def login_user():
    params = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
        'redirect_uri': 'playlistfortwo://login/callback',
        'code': request.form.get('code'),
        'grant_type': 'authorization_code'
    }

    result = requests.post(
        'https://accounts.spotify.com/api/token', data=params)
    if result.status_code != 200:
        return (result.text, result.status_code)
    token = json.loads(result.text)['access_token']

    user_info = requests.get('https://api.spotify.com/v1/me',
                             headers={'Authorization': 'Bearer {}'.format(token)})

    if user_info.status_code != 200:
        return (user_info.text, user_info.status_code)

    user = User.objects(spotify_id=json.loads(user_info.text)['id']).first()

    if not user:
        user = User(
            name=json.loads(user_info.text)['display_name'],
            spotify_id=json.loads(user_info.text)['id'],
            image_links=json.loads(user_info.text)['images'],
            sp_access_token=json.loads(result.text)['access_token'],
            friends=[],
            playlists=[],
            sp_refresh_token=json.loads(result.text)['refresh_token']
        )
        user.save()
    else:
        user.sp_access_token = json.loads(result.text)['access_token']
        user.sp_refresh_token = json.loads(result.text)['refresh_token']
        user.save()

    load_user_data(user)

    encoded_jwt = jwt.encode({'id': user.spotify_id, 'iat': datetime.utcnow(), 'aud': 'client'},
                             os.getenv('JWT_SECRET'),
                             algorithm='HS256')

    return (encoded_jwt, 200)


@app.route('/me', methods=['GET'])
@authorize_user
@check_for_db_errors
def get_logged_in_user_info():
    encoded_jwt = request.headers.get("authorization")
    decoded = jwt.decode(encoded_jwt, os.getenv(
        'JWT_SECRET'), algorithm='HS256', audience="client")

    return find_user_info(decoded['id'])


@app.route('/listening-history', methods=['GET'])
@authorize_user
@confirm_user_identity
@check_for_request_errors
@check_for_db_errors
def get_listening_history():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first()

    if not user:
        return ({'error': F'could not find user with id {user_id}'}, 404)

    days_since_update = datetime.utcnow() - user.song_data.modified

    if not user.song_data.modified or (days_since_update > timedelta(days=7)):
        load_user_data(user)

    return (user.song_data.to_json(), 200)


@app.route('/request-friend', methods=['POST'])
@authorize_user
@confirm_user_identity
@check_for_db_errors
def request_friend():
    user_id = request.form.get("user_id")
    friend_id = request.form.get("friend_id")

    user = User.objects(spotify_id=user_id).first()
    requested = User.objects(spotify_id=friend_id).first()

    if not user:
        return ({'error': F'could not find user with id {user_id}'}, 404)
    elif not requested:
        return ({'error': F'could not find user with id {friend_id}'}, 404)

    if send_friend_request(user, requested):
        return (F"Successfully sent a friend request to user #{friend_id}.", 200)
    else:
        return(F'Could not send friend request to #{friend_id}.', 400)


@app.route('/accept-friend', methods=['POST'])
@authorize_user
@confirm_user_identity
@check_for_db_errors
def accept_friend():
    user_id = request.form.get("user_id")
    friend_id = request.form.get("friend_id")

    accept_friend_request(user_id, friend_id)
    return (F"Successfully added user #{friend_id} as a friend.", 200)


@app.route('/remove-friend', methods=['POST'])
@authorize_user
@confirm_user_identity
@check_for_db_errors
def remove_friend():
    user_id = request.form.get("user_id")
    friend_id = request.form.get("friend_id")

    remove_friend_from_database(user_id, friend_id)
    return (F"Successfully removed user #{friend_id} from friends.", 200)


@app.route('/friends', methods=['GET'])
@authorize_user
@check_for_db_errors
def get_friends():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first()

    if not user:
        return ({'error': F'could not find user with id {user_id}'}, 404)

    response = get_friend_list(user)

    return(json.dumps(response), 200)


@app.route('/user', methods=['GET'])
@authorize_user
@check_for_db_errors
def get__user_info():
    user_id = request.args.get("user_id")
    return find_user_info(user_id)


@app.route('/users', methods=['GET'])
@authorize_user
@check_for_db_errors
def all_users():
    encoded_jwt = request.headers.get("authorization")
    decoded = jwt.decode(encoded_jwt, os.getenv(
        'JWT_SECRET'), algorithm='HS256', audience="client")

    user_uid = decoded['id']
    app_uid = os.getenv('SPOTIFY_USER_ID')

    response = User.objects(spotify_id__nin=[user_uid, app_uid]).only(
        'name', 'spotify_id')

    return(response.to_json(), 200)


@app.route('/genres', methods=['GET'])
@authorize_user
@check_for_db_errors
def user_genres():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first()

    if not user:
        return ({'error': F'could not find user with id {user_id}'}, 404)

    genres = get_user_genres(user)

    return(json.dumps(dict(genres.most_common(20))), 200)


@app.route('/intersection', methods=['GET'])
@authorize_user
@check_for_request_errors
@check_for_db_errors
def find_intersection():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first()
    friend_id = request.args.get("friend_id")
    friend = User.objects(spotify_id=friend_id).first()

    if not user:
        return ({'error': F'could not find user with id {user_id}'}, 404)
    elif not friend:
        return ({'error': F'could not find user with id {friend_id}'}, 404)

    if datetime.utcnow() - user.song_data.modified > timedelta(days=7):
        load_user_data(user)
    if datetime.utcnow() - friend.song_data.modified > timedelta(days=7):
        load_user_data(friend)
    intersection = get_user_intersection(user, friend)
    return(json.dumps(intersection), 200)


@app.route('/recommendations', methods=['GET'])
@authorize_user
@confirm_user_identity
@check_for_request_errors
@check_for_db_errors
def find_reccomendations():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first()
    friend_id = request.args.get("friend_id")
    friend = User.objects(spotify_id=friend_id).first()

    if not user:
        return ({'error': F'could not find user with id {user_id}'}, 404)
    elif not friend:
        return ({'error': F'could not find user with id {friend_id}'}, 404)

    intersection = get_user_intersection(user, friend)
    result = get_rec_from_intersection(intersection)
    return result


@app.route('/playlists', methods=['GET'])
@authorize_user
@confirm_user_identity
@check_for_db_errors
def get_playlists():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first()
    friend_id = request.args.get("friend_id")

    if not user:
        return ({'error': F'could not find user with id {user_id}'}, 404)

    if friend_id:
        playlists = [json.loads(playlist.to_json())
                     for playlist in user.playlists if friend_id in playlist.owners]
    else:
        playlists = [json.loads(playlist.to_json())
                     for playlist in user.playlists]
    return (json.dumps(playlists), 200)


@app.route('/playlist', methods=['GET'])
@authorize_user
@check_for_request_errors
def get_playlist_tracks():
    playlist_id = request.args.get("playlist_id")
    track_list = get_tracks_from_id(playlist_id)
    return (json.dumps(track_list), 200)


@app.route('/new-playlist', methods=['POST'])
@authorize_user
@confirm_user_identity
@check_for_request_errors
@check_for_db_errors
def create_new_playlist():
    user_id = request.args.get("user_id")
    user = User.objects(spotify_id=user_id).first()
    friend_id = request.args.get("friend_id")
    friend = User.objects(spotify_id=friend_id).first()

    filter_explicit = request.args.get("filter_explicit")

    seeds = json.loads(request.form.get('seeds')
                       ) if request.form.get('seeds') else None
    features = json.loads(request.form.get('features')
                          ) if request.form.get('features') else None

    if not user:
        return ({'error': F'could not find user with id {user_id}'}, 404)
    elif not friend:
        return ({'error': F'could not find user with id {friend_id}'}, 404)

    playlist = generate_playlist(
        user, friend, filter_explicit, seeds, features)

    new_playlist = Playlist(
        uri=playlist['uri'],
        description=playlist['description'],
        seeds=playlist['seeds'],
        owners=[user_id, friend_id]
    )

    user.playlists.append(new_playlist)
    friend.playlists.append(new_playlist)
    print(new_playlist.seeds)
    user.save()
    friend.save()
    if new_playlist in user.playlists and new_playlist in friend.playlists:
        return (json.dumps(new_playlist.to_json()), 200)
    else:
        return (json.dumps({"error": "failed to save playlist"}), 400)


@app.route('/edit-playlist', methods=['POST'])
@authorize_user
@check_for_request_errors
@check_for_db_errors
def edit_playlist():
    encoded_jwt = request.headers.get("authorization")
    decoded = jwt.decode(encoded_jwt, os.getenv(
        'JWT_SECRET'), algorithm='HS256', audience="client")

    user_id = decoded['id']

    playlist_uri = request.form.get("playlist_uri")
    if not playlist_uri:
        return (json.dumps({'error': 'playlist uri is a required field'}), 400)

    friend_id = request.form.get('friend_id')

    description = request.form.get('description')

    name = request.form.get('name')

    if description or name:
        success = set_playlist_details(
            description, name, playlist_uri, user_id, friend_id)
    if success:
        return(json.dumps({'success': F'Successfully updated details for  {playlist_uri}'}), 200)
    else:
        return (json.dumps({"error": "failed to update playlist details"}), 400)


@app.route('/delete-playlist', methods=['POST'])
@authorize_user
@check_for_request_errors
@check_for_db_errors
def delete_playlist():
    encoded_jwt = request.headers.get("authorization")
    decoded = jwt.decode(encoded_jwt, os.getenv(
        'JWT_SECRET'), algorithm='HS256', audience="client")

    user_id = decoded['id']

    playlist_uri = request.form.get("playlist_uri")
    if not playlist_uri:
        return (json.dumps({'error': 'playlist_uri is a required field'}), 400)

    success = delete_from_user_playlists(user_id, playlist_uri)
    if success:
        return(json.dumps({'success': F"Successfully deleted {playlist_uri} from {user_id}'s saved playlists"}), 200)
    else:
        return (json.dumps({"error": F"Failed to delete {playlist_uri} from {user_id}'s' saved playlists"}), 400)
