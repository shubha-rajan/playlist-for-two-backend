import json
from unittest.mock import Mock, patch
from nose.tools import assert_list_equal, assert_true

from playlist import helpers

class TestHelpers(object):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('playlist.helpers.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()

    def test_get_top_artists(self):
        self.mock_get.return_value.ok = True
        user = {
            "name":"Verlie Breitenberg",
            "spotify_id":"bdb1ffa9-6c46-4a8a-9d6f-3227b1ab399c",
            "friends":[],
            "image_links":[{"url":"http://placekitten.com/200/300"}],
            "sp_access_token":"98765",
            "sp_refresh_token":"12345"
        }
        
        response = {
            "items" : [ {
                    "external_urls" : {
                    "spotify" : "https://open.spotify.com/artist/0I2XqVXqHScXjHhk6AYYRe"
                    },
                    "followers" : {
                        "href" : None,
                        "total" : 7753
                    },
                    "genres" : [ "swedish hip hop" ],
                    "href" : "https://api.spotify.com/v1/artists/0I2XqVXqHScXjHhk6AYYRe",
                    "id" : "0I2XqVXqHScXjHhk6AYYRe",
                    "images" : [ {
                    "height" : 640,
                    "url" : "https://i.scdn.co/image/2c8c0cea05bf3d3c070b7498d8d0b957c4cdec20",
                    "width" : 640
                    }, {
                    "height" : 300,
                    "url" : "https://i.scdn.co/image/394302b42c4b894786943e028cdd46d7baaa29b7",
                    "width" : 300
                    }, {
                    "height" : 64,
                    "url" : "https://i.scdn.co/image/ca9df7225ade6e5dfc62e7076709ca3409a7cbbf",
                    "width" : 64
                    } ],
                    "name" : "Afasi & Filthy",
                    "popularity" : 54,
                    "type" : "artist",
                    "uri" : "spotify:artist:0I2XqVXqHScXjHhk6AYYRe"
                }],
                "next" : None,
                "previous" : None,
                "total" : 1,
                "limit" : 50,
                "href" : "https://api.spotify.com/v1/me/top/artists"
            }



        result = [{
            'name': "Afasi & Filthy",
            'id': "0I2XqVXqHScXjHhk6AYYRe",
            'images': [ {
                "height" : 640,
                "url" : "https://i.scdn.co/image/2c8c0cea05bf3d3c070b7498d8d0b957c4cdec20",
                "width" : 640
                }, {
                "height" : 300,
                "url" : "https://i.scdn.co/image/394302b42c4b894786943e028cdd46d7baaa29b7",
                "width" : 300
                }, {
                "height" : 64,
                "url" : "https://i.scdn.co/image/ca9df7225ade6e5dfc62e7076709ca3409a7cbbf",
                "width" : 64
                } ],
            'genres':[ "swedish hip hop" ]
        }]
                
        
        
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = response

        top_artists = helpers.get_listening_data(user, 'top_artists')

        assert_list_equal(top_artists, result)

    def test_get_top_tracks(self):
        self.mock_get.return_value.ok = True
        user = {
            "name":"Verlie Breitenberg",
            "spotify_id":"bdb1ffa9-6c46-4a8a-9d6f-3227b1ab399c",
            "friends":[],
            "image_links":[{"url":"http://placekitten.com/200/300"}],
            "sp_access_token":"98765",
            "sp_refresh_token":"12345"
        }
        
        response = {
            "items" : [
                {
                    "artists" : [ {
                    "external_urls" : {
                    "spotify" : "https://open.spotify.com/artist/1VBflYyxBhnDc9uVib98rw"
                    },
                    "href" : "https://api.spotify.com/v1/artists/1VBflYyxBhnDc9uVib98rw",
                    "id" : "1VBflYyxBhnDc9uVib98rw",
                    "name" : "Icona Pop",
                    "type" : "artist",
                    "uri" : "spotify:artist:1VBflYyxBhnDc9uVib98rw"
                } ],
                    "disc_number" : 1,
                    "duration_ms" : 187026,
                    "explicit" : False,
                    "external_urls" : {
                        "spotify" : "https://open.spotify.com/track/15iosIuxC3C53BgsM5Uggs"
                    },
                    "href" : "https://api.spotify.com/v1/tracks/15iosIuxC3C53BgsM5Uggs",
                    "id" : "15iosIuxC3C53BgsM5Uggs",
                    "is_playable" : True,
                    "name" : "All Night",
                    "preview_url" : "https://p.scdn.co/mp3-preview/9ee589fa7fe4e96bad3483c20b3405fb59776424",
                    "track_number" : 2,
                    "type" : "track",
                    "uri" : "spotify:track:15iosIuxC3C53BgsM5Uggs"
                }
            ],
                "next" : None,
                "previous" : None,
                "total" : 1,
                "limit" : 50,
                "href" : "https://api.spotify.com/v1/me/top/artists"
            }



        result = [{
            'name': "All Night",
            'id': "15iosIuxC3C53BgsM5Uggs",
            'artists': [ '1VBflYyxBhnDc9uVib98rw' ],
            'explicit': False,
        }]
                
        
        
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = response

        top_artists = helpers.get_listening_data(user, 'top_songs')

        assert_list_equal(top_artists, result)



