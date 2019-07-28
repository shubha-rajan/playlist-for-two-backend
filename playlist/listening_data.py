from collections import Counter
import requests

from .helpers import refresh_token


def get_listening_data(user, data_type):
    endpoints = {
        'saved_songs': 'https://api.spotify.com/v1/me/tracks?offset=0&limit=50',
        'top_songs': 'https://api.spotify.com/v1/me/top/tracks?offset=0&limit=50',
        'top_artists': 'https://api.spotify.com/v1/me/top/artists?offset=0&limit=50',
        'followed_artists': 'https://api.spotify.com/v1/me/following?type=artist&limit=50'
    }

    url = endpoints[data_type]
    returned_list = []
    access_token = user['sp_access_token']

    while url:
        response = requests.get(url, headers={
            'Authorization': F'Bearer {access_token}'})
        if response.status_code == 401:
            refresh_token(user['spotify_id'])
        elif data_type == 'followed_artists':
            returned_list += response.json()['artists']['items']
            url = response.json()['artists']['next']
        else:
            returned_list += response.json()['items']
            url = response.json()['next']

    if data_type == 'followed_artists' or data_type == 'top_artists':
        returned_list = [clean_artist_data(artist) for artist in returned_list]
    elif data_type == 'saved_songs' or data_type == 'top_songs':
        returned_list = [clean_song_data(track) for track in returned_list]

    return returned_list


def load_user_data(user):
    user['song_data']['saved_songs'] = get_listening_data(user, 'saved_songs')
    user['song_data']['top_songs'] = get_listening_data(user, 'top_songs')
    user['song_data']['top_artists'] = get_listening_data(user, 'top_artists')
    user['song_data'].followed_artists = get_listening_data(
        user, 'followed_artists')
    user.save()


def clean_artist_data(artist):
    return({
        'name': artist['name'],
        'id': artist['id'],
        'images': artist['images'],
        'genres': artist['genres']
    })


def clean_song_data(track):
    if 'track' in track:
        track = track['track']
    track = {
        'name': track['name'],
        'id': track['id'],
        'artists': [{'id': artist['id'], 'name':artist['name']} for artist in track['artists']],
        'explicit': track['explicit']
    }
    return track


def get_user_genres(user):
    user_artists = user['song_data']['top_artists'] + \
        user['song_data']['followed_artists']
    user_genres = [
        genre for artist in user_artists for genre in artist['genres']]
    return Counter(user_genres)


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
    return features


def get_song_analysis_matrix(user):
    token = refresh_token(user.spotify_id)
    song_ids = ','.join([song['id']
                         for song in user['song_data']['top_songs']])

    response = requests.get(F'https://api.spotify.com/v1/audio-features/?ids={song_ids}',
                            headers={'Authorization': F'Bearer {token}'})

    if response.status_code == 200:
        song_analysis_matrix = [get_features(
            track) for track in response.body['audio_features']]
        return song_analysis_matrix
    else:
        response.raise_for_status()
