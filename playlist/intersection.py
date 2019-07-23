from .listening_data import load_user_data, get_user_genres


def find_common_songs(user1, user2):
    user1_songs = user1['song_data']['top_songs'] + user1['song_data']['saved_songs']
    user2_songs = user2['song_data']['top_songs']+ user2['song_data']['saved_songs']

    user1_songs = set([song['id'] for song in user1_songs])
    user2_songs = set([song['id'] for song in user2_songs])

    return(list(user1_songs.intersection(user2_songs)))

def find_common_artists(user1, user2):
    user1_songs = user1['song_data']['top_songs'] + user1['song_data']['saved_songs']
    user1_artists_from_songs =  [artist for song in user1_songs for artist in song['artists'] ]
    user1_artists = user1['song_data']['top_artists'] + user1['song_data']['followed_artists'] 

    user2_songs = user2['song_data']['top_songs'] + user2['song_data']['saved_songs']
    user2_artists_from_songs =  [artist for song in user2_songs for artist in song['artists'] ]
    user2_artists = user2['song_data']['top_artists'] + user2['song_data']['followed_artists']

    user1_artists = set([artist['id'] for artist in user1_artists] + user1_artists_from_songs)
    user2_artists = set([artist['id'] for artist in user2_artists] + user2_artists_from_songs)

    return(list(user1_artists & user2_artists))



def find_common_genres(user1, user2):
    user1_top_genres = set(dict(get_user_genres(user1).most_common()).keys())
    user2_top_genres = set(dict(get_user_genres(user2).most_common()).keys())

    return(list(user1_top_genres & user2_top_genres))

def get_user_intersection(user1, user2):

    intersection = {
        'common_songs': find_common_songs(user1, user2),
        'common_artists':find_common_artists(user1, user2),
        'common_genres': find_common_genres(user1, user2)
    }
    return(intersection)    
    