from .models import User, Friendship


def send_friend_request(user, requested):
    outgoing_request = Friendship(
        status='requested',
        friend_id=requested.spotify_id,
        name=requested.name
    )
    user.friends.append(
        outgoing_request
    )

    incoming_request = Friendship(
        status='pending',
        friend_id=user.spotify_id,
        name=user.name
    )
    requested.friends.append(
        incoming_request
    )

    user.save()
    requested.save()
    if outgoing_request in user.friends and incoming_request in requested.friends:
        return True
    else:
        return False


def accept_friend_request(user_id, friend_id):
    User.objects(spotify_id=user_id,
                 friends__friend_id=friend_id,
                 friends__status='pending').update_one(set__friends__S__status='accepted')

    User.objects(spotify_id=friend_id,
                 friends__friend_id=user_id,
                 friends__status='requested').update_one(set__friends__S__status='accepted')


def remove_friend_from_database(user_id, friend_id):
    print(friend_id)

    User.objects(spotify_id=user_id).update_one(
        pull__friends__friend_id=friend_id)

    User.objects(spotify_id=friend_id).update_one(
        pull__friends__friend_id=user_id)


def get_friend_list(user):
    incoming_requests = [friend.to_json()
                         for friend in user.friends if friend.status == 'pending']
    sent_requests = [friend.to_json()
                     for friend in user.friends if friend.status == 'requested']
    accepted_requests = [friend.to_json()
                         for friend in user.friends if friend.status == 'accepted']

    response = {
        "user": user.spotify_id,
        "friends": {
            "incoming": incoming_requests,
            "sent": sent_requests,
            "accepted": accepted_requests,
        }
    }
    return response
