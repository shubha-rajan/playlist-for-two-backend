from datetime import datetime
from mongoengine import (Document, EmbeddedDocument,
                         DateTimeField, ListField, DictField, EmbeddedDocumentField, StringField)
from mongoengine import signals


def update_modified(document):
    document.modified = datetime.utcnow()


class SongData(EmbeddedDocument):
    modified = DateTimeField(default=datetime.utcnow)
    saved_songs = ListField(DictField())
    followed_artists = ListField(DictField())
    top_songs = ListField(DictField())
    top_artists = ListField(DictField())

    signals.pre_save.connect(update_modified, sender='User')


class Friendship(EmbeddedDocument):
    status = StringField(required=True, choices=(
        "requested", "pending", "accepted"))
    modified = DateTimeField(default=datetime.utcnow)
    friend_id = StringField(required=True)
    name = StringField()

    signals.pre_save.connect(update_modified, sender='User')


class Playlist(EmbeddedDocument):
    uri = StringField(required=True)
    owners = ListField(StringField())
    description = DictField()
    seeds = ListField(StringField())


class User(Document):
    name = StringField(required=True)
    spotify_id = StringField(required=True)
    sp_access_token = StringField()
    sp_refresh_token = StringField()
    image_links = ListField(DictField())
    friends = ListField(EmbeddedDocumentField(Friendship))
    song_data = EmbeddedDocumentField(SongData, default=SongData)
    playlists = ListField(EmbeddedDocumentField(Playlist))
