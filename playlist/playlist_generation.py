import os
import random
from datetime import datetime
import json
import requests


from .helpers import refresh_token
from .intersection import get_user_intersection
from .listening_data import clean_song_data
from .models import User


def clean_playlist_track_data(track):
    if 'track' in track:
        track = track['track']
    return (
        {
            'name': track['name'],
            'id': track['id'],
            'artists': [artist['name'] for artist in track['artists']]
        }
    )


def get_seeds(intersection):
    songs = [{song['id']: 'song'} for song in intersection['common_songs']]
    artists = [{artist['id']: 'artist'}
               for artist in intersection['common_artists']]
    genres = [{genre: 'genre'} for genre in intersection['common_genres']]

    if len(songs + artists + genres) > 5:
        seeds = random.sample((songs + artists + genres), 5)
    else:
        seeds = songs + artists + genres
    return seeds


def get_filtered_recommendations(url, token):
    tracks = []

    while len(tracks) < 20:
        response = requests.get(
            url, headers={'Authorization': F'Bearer {token}'})
        if response.status_code != 200:
            response.raise_for_status()
        tracks += [track for track in response.json()['tracks']
                   if not track['explicit']]
    return random.sample(tracks, 20)


def send_recommendation_request(request_url, token, filter_explicit):
    tracks = []
    if filter_explicit:
        tracks = get_filtered_recommendations(request_url, token)
    else:
        response = requests.get(request_url, headers={
                                'Authorization': F'Bearer {token}'})
        if response.status_code != 200:
            response.raise_for_status()
        tracks = response.json()['tracks']
        return tracks


def get_rec_from_seeds(seeds, features, filter_explicit=False):
    token = refresh_token(os.getenv('SPOTIFY_USER_ID'))

    seed_songs = ','.join(seeds['songs'])
    seed_artists = ','.join(seeds['artists'])
    seed_genres = ','.join(seeds['genres'])

    request_url = 'https://api.spotify.com/v1/recommendations?'
    request_url += F'seed_tracks={seed_songs}&seed_artists={seed_artists}&seed_genres={seed_genres}'

    feature_names = []

    for feature, value in features.items():
        feature_min = value['min']
        feature_max = value['max']
        request_url += F'&{feature}_min={feature_min}&{feature}_max={feature_max}'
        feature_names.append(
            F'{feature}: {round(feature_min, 2)} - {round(feature_max, 2)}')

    tracks = send_recommendation_request(request_url, token, filter_explicit)

    seed_ids = [{song: 'song'} for song in seeds['songs']]
    seed_ids += [{artist: 'artist'} for artist in seeds['artists']]
    seed_ids += [{genre: 'genre'} for genre in seeds['genres']]
    seed_names = get_seed_names(seed_ids, token)

    recommendations = {'seeds': seed_names,
                       'features': feature_names,
                       'recommendations': [clean_song_data(track) for track in tracks]
                       }

    return recommendations


def get_rec_from_intersection(intersection, filter_explicit=False):
    token = refresh_token(os.getenv('SPOTIFY_USER_ID'))
    seeds = get_seeds(intersection)

    seed_songs = ','.join([list(item.keys())[0]
                           for item in seeds if 'song' in item.values()])
    seed_artists = ','.join([list(item.keys())[0]
                             for item in seeds if 'artist' in item.values()])
    seed_genres = ','.join([list(item.keys())[0]
                            for item in seeds if 'genre' in item.values()])

    request_url = 'https://api.spotify.com/v1/recommendations?'
    request_url += F'seed_tracks={seed_songs}&seed_artists={seed_artists}&seed_genres={seed_genres}'

    seed_names = get_seed_names(seeds, token)

    tracks = send_recommendation_request(request_url, token, filter_explicit)

    recommendations = {'seeds': seed_names,
                       'recommendations': [clean_song_data(track) for track in tracks]
                       }

    return recommendations


def get_seed_names(seeds, token):
    seed_names = []

    for seed in seeds:
        if 'song' in seed.values():
            song_id = list(seed.keys())[0]
            song_name = name_from_id(song_id, 'track', token)
            seed_names.append(F'{song_name} (song)')
        elif 'artist' in seed.values():
            artist_id = list(seed.keys())[0]
            artist_name = name_from_id(artist_id, 'artist', token)
            seed_names.append(F'{artist_name} (artist)')
        else:
            genre = list(seed.keys())[0]
            seed_names.append(F'{genre} (genre)')
    return seed_names


def name_from_id(object_id, object_type, token=None):
    if not token:
        token = refresh_token(os.getenv('SPOTIFY_USER_ID'))
    response = requests.get(F'https://api.spotify.com/v1/{object_type}s/{object_id}',
                            headers={'Authorization': F'Bearer {token}'})
    if response.status_code != 200:
        response.raise_for_status()
    else:
        return response.json()['name']


def generate_playlist(user1, user2, filter_explicit, seeds=None, features=None, ):
    uid = os.getenv('SPOTIFY_USER_ID')

    if not seeds and not features:
        intersection = get_user_intersection(user1, user2)
        recommendations = get_rec_from_intersection(
            intersection, filter_explicit)
    else:
        recommendations = get_rec_from_seeds(seeds, features, filter_explicit)

    seed_names = recommendations['seeds']
    recommendation_list = recommendations['recommendations']

    token = refresh_token(uid)

    dt = datetime.now().strftime("%B %d, %Y %I:%M%p")

    playlist_info = {
        'name': F"{dt} - {user1.name} and {user2.name}'s Playlist for Two",
        'public': 'false',
        'collaborative': 'false',
        'description': (
            "This playlist was generated by Spotify and the Playlist for Two app based on common " +
            F"songs, artists and genres in {user1.name} and {user2.name}'s music libraries. " +
            F"The seeds used to generate this playlist are {', '.join(seed_names)}"
        )
    }

    if 'features' in recommendations:
        playlist_info['description'] += F", {', '.join(recommendations['features'])}"

    create_playlist = requests.post(F'https://api.spotify.com/v1/users/{uid}/playlists',
                                    headers={
                                        'Authorization': F'Bearer {token}'},
                                    data=json.dumps(playlist_info))

    if create_playlist.status_code != 200:
        create_playlist.raise_for_status()

    pl_id = create_playlist.json()['id']

    tracks = ','.join(['spotify:track:{}'.format(track['id'])
                       for track in recommendation_list])

    add_tracks = requests.post(F'https://api.spotify.com/v1/playlists/{pl_id}/tracks?uris={tracks}',
                               headers={'Authorization': F'Bearer {token}'})

    if add_tracks.status_code == 200 or add_tracks.status_code == 201:
        return {'seeds': seed_names,
                'uri': F'spotify:playlist:{pl_id}',
                'description': playlist_info}
    else:
        add_tracks.raise_for_status()


def get_tracks_from_id(playlist_id):
    token = refresh_token(os.getenv('SPOTIFY_USER_ID'))
    response = requests.get(F'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
                            headers={'Authorization': F'Bearer {token}'})

    if response.status_code == 200:
        tracks = response.json()['items']
        tracks = [clean_playlist_track_data(track) for track in tracks]
        return tracks
    else:
        response.raise_for_status()


def set_playlist_details(description, name, playlist_uri, user_id, friend_id):
    token = refresh_token(os.getenv('SPOTIFY_USER_ID'))
    playlist_id = playlist_uri[17:]

    payload = {}
    if name and description:
        payload = {"description": description, "name": name}
    elif name:
        payload = {'name': name}
    elif description:
        payload = {'description': description}
    else:
        return False

    response = requests.put(F'https://api.spotify.com/v1/playlists/{playlist_id}',
                            headers={'Authorization': F'Bearer {token}'},
                            data=json.dumps(payload))

    if response.status_code != 200:
        response.raise_for_status()

    if name:
        User.objects(spotify_id=user_id,
                     playlists__uri=playlist_uri).update(set__playlists__S__description__name=name)
        User.objects(spotify_id=friend_id,
                     playlists__uri=playlist_uri).update(set__playlists__S__description__name=name)

    if description:
        User.objects(spotify_id=user_id,
                     playlists__uri=playlist_uri).update(
                         set__playlists__S__description__description=description)
        User.objects(spotify_id=friend_id,
                     playlists__uri=playlist_uri).update(
                         set__playlists__S__description__description=description)

    return True
