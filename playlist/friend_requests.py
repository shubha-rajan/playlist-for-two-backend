from .models import User, SongData, Friendship, Playlist

def send_friend_request(user, requested):
    user.friends.append(
        Friendship(
                status='requested',
                friend_id=friend_id,
                name=requested.name
        )
    )
    user.save()

        
    requested.friends.append(
        Friendship(
                status='pending',
                friend_id=user_id,
                name=user.name
        )
    )
    requested.save()

    return True

def accept_friend_request(user_id, friend_id):
    User.objects.filter(spotify_id=user_id, friends__friend_id=friend_id).update(set__friends__S__status='accepted')

    User.objects.filter(spotify_id=friend_id, friends__friend_id=user_id).update(set__friends__S__status='accepted')

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