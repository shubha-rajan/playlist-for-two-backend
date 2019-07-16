from mongoengine import *
import datetime

class SongData(EmbeddedDocument):
    saved_songs=ListField(DictField())
    followed_artists=ListField(DictField())
    top_songs=ListField(DictField())
    top_artists=ListField(DictField())

class Friendship(EmbeddedDocument):
    status= StringField(required=True, choices=("requested", "pending", "accepted"))
    modified= DateTimeField(default=datetime.datetime.utcnow)
    friend_id = StringField(required=True)
    name = StringField()

class User(Document):
    name= StringField(required=True)
    spotify_id= StringField(required=True)
    sp_access_token=StringField()
    sp_refresh_token=StringField()
    image_links=ListField(DictField())
    friends= ListField(EmbeddedDocumentField(Friendship))
    song_data= EmbeddedDocumentField(SongData, default=SongData)





class Playlist(Document):
    uri= StringField(required=True)
    owners= ListField(ReferenceField(User))