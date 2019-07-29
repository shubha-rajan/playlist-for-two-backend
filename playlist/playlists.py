import os
from datetime import datetime
import json
import requests


from .helpers import refresh_token
from .intersection import get_user_intersection

from .recommendations import get_rec_from_intersection, get_rec_from_seeds
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
    print(friend_id)
    if name:
        User.objects(spotify_id=user_id,
                     playlists__uri=playlist_uri).update(set__playlists__S__description__name=name)
        User.objects(spotify_id=friend_id,
                     playlists__uri=playlist_uri).update(set__playlists__S__description__name=name)

    if description:
        User.objects(spotify_id=user_id,
                     playlists__uri=playlist_uri).update_one(
                         set__playlists__S__description__description=description)
        User.objects(spotify_id=friend_id,
                     playlists__uri=playlist_uri).update_one(
                         set__playlists__S__description__description=description)

    return True


def delete_from_user_playlists(user_id, playlist_uri):
    User.objects(spotify_id=user_id).update_one(
        pull__playlists__uri=playlist_uri)

    return True
