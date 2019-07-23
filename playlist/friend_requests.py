from .models import User, SongData, Friendship, Playlist

from mongoengine import Document

def send_friend_request(user, requested):
    user.friends.append(
        Friendship(
                status='requested',
                friend_id=friend_id,
                name=requested.name
        )
    )

    requested.friends.append(
        Friendship(
                status='pending',
                friend_id=user_id,
                name=user.name
        )
    )
    
    if user.save() and requested.save():
        return True
    else
        return False

def accept_friend_request(user_id, friend_id):
    try:
        User.objects.get(spotify_id=user_id, friends__friend_id=friend_id, friends__status='pending').update(set__friends__S__status='accepted')
    except Document.DoesNotExist as err:
        print(err)
        return False
    except Document.MultipleObjectsReturned as err:
        print(err)
        return False

    try:
        User.objects.get(spotify_id=friend_id, friends__friend_id=user_id, friends__status='requested').update(set__friends__S__status='accepted')
    except Document.DoesNotExist as err:
        print(err)
        return False
    except Document.MultipleObjectsReturned as err:
        print(err)
        return False

    return True

def get_friend_list(user):
    incoming_requests= [friend.to_json() for friend in user.friends if friend.status=='pending']
    sent_requests= [friend.to_json() for friend in user.friends if friend.status=='requested']
    accepted_requests= [friend.to_json() for friend in user.friends if friend.status=='accepted']

    response = {
        "user":user.spotify_id, 
        "friends": {
            "incoming":incoming_requests,
            "sent":sent_requests,
            "accepted":accepted_requests,
        }
    }
    return response