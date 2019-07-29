import os
import random

import requests


from .helpers import refresh_token

from .listening_data import clean_song_data


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
