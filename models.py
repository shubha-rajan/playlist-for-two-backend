from mongoengine import *
import datetime

class SongData(EmbeddedDocument):
    saved_songs=ListField(DictField())
    recently_played=ListField(DictField())
    top_songs=ListField(DictField())
    top_artists=ListField(DictField())

class User(Document):
    name= StringField(required=True)
    spotify_id= StringField(required=True)
    access_token=StringField()
    refresh_token=StringField()
    image_links=ListField(DictField())
    friends= ListField(ReferenceField('Friendship'))
    song_data= EmbeddedDocumentField(SongData, default=SongData)


class Friendship(Document):
    status= StringField(required=True, choices=("requested", "pending", "accepted"))
    modified= DateTimeField(default=datetime.datetime.utcnow)
    user= ReferenceField(User)


class Playlist(Document):
    uri= StringField(required=True)
    owners= ListField(ReferenceField(User))