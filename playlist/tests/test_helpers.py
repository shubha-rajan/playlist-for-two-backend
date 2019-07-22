import json
from unittest.mock import Mock, patch
from unittest import TestCase
from playlist import helpers

class TestFindIntersection(TestCase): 
    @classmethod
    def setup_class(cls):
        cls.song_data= {
            'saved_songs':[],
            'followed_artists': [
                {
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
                }, 
            ],
            'top_songs': [
            {
                'name': "All Night",
                'id': "15iosIuxC3C53BgsM5Uggs",
                'artists': [ '1VBflYyxBhnDc9uVib98rw' ],
                'explicit': False,
            }
            ],
            'top_artists': [
                {
                    'name': "David Bowie",
                    'id': "0oSGxfWSnnOXhD2fKuz2Gy",
                    'images': [ {
                        "height" : 1000,
                        "url" : "https://i.scdn.co/image/32bd9707b42a2c081482ec9cd3ffa8879f659f95",
                        "width" : 1000
                        }, {
                        "height" : 640,
                        "url" : "https://i.scdn.co/image/865f24753e5e4f40a383bf24a9cdda598a4559a8",
                        "width" : 640
                        }, {
                        "height" : 200,
                        "url" : "https://i.scdn.co/image/7ddd6fa5cf78aee2f2e8b347616151393022b7d9",
                        "width" : 200
                        }, {
                        "height" : 64,
                        "url" : "https://i.scdn.co/image/c8dc28c191432862afce298216458a6f00bbfbd8",
                        "width" : 64
                        } ],
                    'genres':[ "art rock", "glam rock", "permanent wave" ]
                }
            ],
        }
        cls.user1 = {"name":"Nellie Klocko","spotify_id":"832e0f77-b319-40bd-9ef4-4fdd2206e11a","friends":[],"image_links":[{"url":"http://placekitten.com/200/300"}],'song_data': cls.song_data}
        cls.user2 = {"name":"Helga Schuster","spotify_id":"70bb54ad-444b-4e1f-a0a6-033d04e1eab2","friends":[],"image_links":[{"url":"http://placekitten.com/200/300"}], 'song_data': cls.song_data}
        
  
    def test_find_common_artists(self):
        result = ["0I2XqVXqHScXjHhk6AYYRe", "0oSGxfWSnnOXhD2fKuz2Gy", "1VBflYyxBhnDc9uVib98rw"]
        common_artists = helpers.find_common_artists(self.user1, self.user2)
        for artist_id in result:
            self.assertIn(artist_id, common_artists)

    def test_find_common_songs(self):
        result = ["15iosIuxC3C53BgsM5Uggs"]
        common_songs = helpers.find_common_songs(self.user1, self.user2)
        for artist_id in result:
            self.assertIn(artist_id, common_songs)

    def test_find_common_genres(self):
        result = ["15iosIuxC3C53BgsM5Uggs"]
        common_genres = helpers.find_common_genres(self.user1, self.user2)
        for genre in result:
            self.assertIn(genres, common_genres)


class TestGetListeningDataHelpers(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('playlist.helpers.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()
        cls.user = {
            "name":"Verlie Breitenberg",
            "spotify_id":"bdb1ffa9-6c46-4a8a-9d6f-3227b1ab399c",
            "friends":[],
            "image_links":[{"url":"http://placekitten.com/200/300"}],
            "sp_access_token":"98765",
            "sp_refresh_token":"12345"
        }

    def test_get_top_artists_response_ok(self):
        self.mock_get.return_value.ok = True
        
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

        top_artists = helpers.get_listening_data(self.user, 'top_artists')

        self.assertListEqual(top_artists, result)

    def test_get_top_tracks_response_ok(self):
        self.mock_get.return_value.ok = True

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

        top_artists = helpers.get_listening_data(self.user, 'top_songs')

        self.assertListEqual(top_artists, result)

    def test_get_saved_tracks_response_ok(self):

        self.mock_get.return_value.ok = True

        response = {
            "items" : [ {
                "added_at" : "2016-10-24T15:03:07Z",
                "track" : {
                "album" : {
                    "album_type" : "album",
                    "artists" : [ {
                    "external_urls" : {
                        "spotify" : "https://open.spotify.com/artist/0LIll5i3kwo5A3IDpipgkS"
                    },
                    "href" : "https://api.spotify.com/v1/artists/0LIll5i3kwo5A3IDpipgkS",
                    "id" : "0LIll5i3kwo5A3IDpipgkS",
                    "name" : "Squirrel Nut Zippers",
                    "type" : "artist",
                    "uri" : "spotify:artist:0LIll5i3kwo5A3IDpipgkS"
                    } ],
                    "available_markets" : [ "AD", "AR", "AT", "AU", "BE", "BG", "BO", "BR", "CH", "CL", "CO", "CR", "CY", "CZ", "DE", "DK", "DO", "EC", "EE", "ES", "FI", "FR", "GB", "GR", "GT", "HK", "HN", "HU", "ID", "IE", "IS", "IT", "JP", "LI", "LT", "LU", "LV", "MC", "MT", "MY", "NI", "NL", "NO", "NZ", "PA", "PE", "PH", "PL", "PT", "PY", "SE", "SG", "SK", "SV", "TR", "TW", "UY" ],
                    "external_urls" : {
                    "spotify" : "https://open.spotify.com/album/63GBbuUNBel2ovJjUrfh5r"
                    },
                    "href" : "https://api.spotify.com/v1/albums/63GBbuUNBel2ovJjUrfh5r",
                    "id" : "63GBbuUNBel2ovJjUrfh5r",
                    "images" : [ {
                    "height" : 640,
                    "url" : "https://i.scdn.co/image/e9c5fd63935b08ed27a7a5b0e65b2c6bf600fc4a",
                    "width" : 640
                    }, {
                    "height" : 300,
                    "url" : "https://i.scdn.co/image/416b6589d9e2d91147ff5072d640d0041b04cb41",
                    "width" : 300
                    }, {
                    "height" : 64,
                    "url" : "https://i.scdn.co/image/4bb6b451b8edde5881a5fcbe1a54bc8538f407ec",
                    "width" : 64
                    } ],
                    "name" : "The Best of Squirrel Nut Zippers",
                    "type" : "album",
                    "uri" : "spotify:album:63GBbuUNBel2ovJjUrfh5r"
                },
                "artists" : [ {
                    "external_urls" : {
                    "spotify" : "https://open.spotify.com/artist/0LIll5i3kwo5A3IDpipgkS"
                    },
                    "href" : "https://api.spotify.com/v1/artists/0LIll5i3kwo5A3IDpipgkS",
                    "id" : "0LIll5i3kwo5A3IDpipgkS",
                    "name" : "Squirrel Nut Zippers",
                    "type" : "artist",
                    "uri" : "spotify:artist:0LIll5i3kwo5A3IDpipgkS"
                } ],
                "available_markets" : [ "AD", "AR", "AT", "AU", "BE", "BG", "BO", "BR", "CH", "CL", "CO", "CR", "CY", "CZ", "DE", "DK", "DO", "EC", "EE", "ES", "FI", "FR", "GB", "GR", "GT", "HK", "HN", "HU", "ID", "IE", "IS", "IT", "JP", "LI", "LT", "LU", "LV", "MC", "MT", "MY", "NI", "NL", "NO", "NZ", "PA", "PE", "PH", "PL", "PT", "PY", "SE", "SG", "SK", "SV", "TR", "TW", "UY" ],
                "disc_number" : 1,
                "duration_ms" : 137040,
                "explicit" : False,
                "external_ids" : {
                    "isrc" : "USMA20215185"
                },
                "external_urls" : {
                    "spotify" : "https://open.spotify.com/track/2jpDioAB9tlYXMdXDK3BGl"
                },
                "href" : "https://api.spotify.com/v1/tracks/2jpDioAB9tlYXMdXDK3BGl",
                "id" : "2jpDioAB9tlYXMdXDK3BGl",
                "name" : "Good Enough For Granddad",
                "popularity" : 19,
                "preview_url" : "https://p.scdn.co/mp3-preview/32cc6f7a3fca362dfcde753f0339f42539f15c9a",
                "track_number" : 1,
                "type" : "track",
                "uri" : "spotify:track:2jpDioAB9tlYXMdXDK3BGl"
                }
                }
            ],
            "limit": 50,
            "next": None,
            "offset": 0,
            "previous": None,
            "total": 1
            }

        result = [{
            'name': "Good Enough For Granddad",
            'id': "2jpDioAB9tlYXMdXDK3BGl",
            'artists': [ "0LIll5i3kwo5A3IDpipgkS" ],
            'explicit': False,
        }]
                
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = response

        top_artists = helpers.get_listening_data(self.user, 'saved_songs')

        self.assertListEqual(top_artists, result)

    def test_get_followed_artists_response_ok(self):
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
            "artists" : {
                "items": [ {
                    "external_urls" : {
                    "spotify" : "https://open.spotify.com/artist/0oSGxfWSnnOXhD2fKuz2Gy"
                    },
                    "followers" : {
                    "href" : None,
                    "total" : 633494
                    },
                    "genres" : [ "art rock", "glam rock", "permanent wave" ],
                    "href" : "https://api.spotify.com/v1/artists/0oSGxfWSnnOXhD2fKuz2Gy",
                    "id" : "0oSGxfWSnnOXhD2fKuz2Gy",
                    "images" : [ {
                        "height" : 1000,
                        "url" : "https://i.scdn.co/image/32bd9707b42a2c081482ec9cd3ffa8879f659f95",
                        "width" : 1000
                        }, {
                        "height" : 640,
                        "url" : "https://i.scdn.co/image/865f24753e5e4f40a383bf24a9cdda598a4559a8",
                        "width" : 640
                        }, {
                        "height" : 200,
                        "url" : "https://i.scdn.co/image/7ddd6fa5cf78aee2f2e8b347616151393022b7d9",
                        "width" : 200
                        }, {
                        "height" : 64,
                        "url" : "https://i.scdn.co/image/c8dc28c191432862afce298216458a6f00bbfbd8",
                        "width" : 64
                        } ],
                    "name" : "David Bowie",
                    "popularity" : 77,
                    "type" : "artist",
                    "uri" : "spotify:artist:0oSGxfWSnnOXhD2fKuz2Gy"
                }],
                "next" : None,
                "total" : 1,
                "cursors" : {},
                "limit" : 50,
                "href" : "https://api.spotify.com/v1/users/thelinmichael/following?type=artist&limit=20"
            },
        }
        



        result = [{
                    'name': "David Bowie",
                    'id': "0oSGxfWSnnOXhD2fKuz2Gy",
                    'images': [ {
                        "height" : 1000,
                        "url" : "https://i.scdn.co/image/32bd9707b42a2c081482ec9cd3ffa8879f659f95",
                        "width" : 1000
                        }, {
                        "height" : 640,
                        "url" : "https://i.scdn.co/image/865f24753e5e4f40a383bf24a9cdda598a4559a8",
                        "width" : 640
                        }, {
                        "height" : 200,
                        "url" : "https://i.scdn.co/image/7ddd6fa5cf78aee2f2e8b347616151393022b7d9",
                        "width" : 200
                        }, {
                        "height" : 64,
                        "url" : "https://i.scdn.co/image/c8dc28c191432862afce298216458a6f00bbfbd8",
                        "width" : 64
                        } ],
                    'genres':[ "art rock", "glam rock", "permanent wave" ]
                }]
                
        
        
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = response

        top_artists = helpers.get_listening_data(user, 'followed_artists')

        self.assertListEqual(top_artists, result)


