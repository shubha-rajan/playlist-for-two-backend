from unittest.mock import Mock, patch
from unittest import TestCase
from playlist import playlist_generation

# Mock API data from Spotify API Docs :
# https://developer.spotify.com/documentation/web-api/reference/

class TestPlaylistGeneration(TestCase):
    
    @classmethod
    def setup_class(cls):
        cls.mock_get_user_intersection_patcher = patch('playlist.playlist_generation.get_user_intersection')
        cls.mock_refresh_token_patcher = patch('playlist.playlist_generation.refresh_token')
        cls.mock_get_patcher = patch('playlist.playlist_generation.requests.get')
        cls.mock_get_seeds_patcher = patch('playlist.playlist_generation.get_seeds')
        cls.mock_get_seed_names_patcher = patch('playlist.playlist_generation.get_seed_names')
        cls.mock_refresh_token = cls.mock_refresh_token_patcher.start()
        cls.mock_get = cls.mock_get_patcher.start()
        cls.mock_get_seeds = cls.mock_get_seeds_patcher.start()
        cls.mock_get_seed_names = cls.mock_get_seed_names_patcher.start()
    
    @classmethod
    def teardown_class(cls):
        cls.mock_get.stop()
        cls.mock_refresh_token.stop()
        cls.mock_get_seeds.stop()
        cls.mock_get_seed_names.stop()

    def test_get_recommendations(self):
        self.maxDiff =None
        intersection = {
        'common_songs': ["15iosIuxC3C53BgsM5Uggs"],
        'common_artists':["0I2XqVXqHScXjHhk6AYYRe", "0oSGxfWSnnOXhD2fKuz2Gy", "1VBflYyxBhnDc9uVib98rw"],
        'common_genres': ["swedish hip hop", "art rock", "glam rock", "permanent wave"],
        }

        seeds = [{"glam rock":"genre"}, {"1VBflYyxBhnDc9uVib98rw": "artist"}, {"permanent wave": "genre"},{"15iosIuxC3C53BgsM5Uggs":"song"}]

        response = {
            "tracks": [
                {
                "artists" : [ {
                    "external_urls" : {
                    "spotify" : "https://open.spotify.com/artist/134GdR5tUtxJrf8cpsfpyY"
                    },
                    "href" : "https://api.spotify.com/v1/artists/134GdR5tUtxJrf8cpsfpyY",
                    "id" : "134GdR5tUtxJrf8cpsfpyY",
                    "name" : "Elliphant",
                    "type" : "artist",
                    "uri" : "spotify:artist:134GdR5tUtxJrf8cpsfpyY"
                }, {
                    "external_urls" : {
                    "spotify" : "https://open.spotify.com/artist/1D2oK3cJRq97OXDzu77BFR"
                    },
                    "href" : "https://api.spotify.com/v1/artists/1D2oK3cJRq97OXDzu77BFR",
                    "id" : "1D2oK3cJRq97OXDzu77BFR",
                    "name" : "Ras Fraser Jr.",
                    "type" : "artist",
                    "uri" : "spotify:artist:1D2oK3cJRq97OXDzu77BFR"
                } ],
                "disc_number" : 1,
                "duration_ms" : 199133,
                "explicit" : False,
                "external_urls" : {
                    "spotify" : "https://open.spotify.com/track/1TKYPzH66GwsqyJFKFkBHQ"
                },
                "href" : "https://api.spotify.com/v1/tracks/1TKYPzH66GwsqyJFKFkBHQ",
                "id" : "1TKYPzH66GwsqyJFKFkBHQ",
                "is_playable" : True,
                "name" : "Music Is Life",
                "preview_url" : "https://p.scdn.co/mp3-preview/546099103387186dfe16743a33edd77e52cec738",
                "track_number" : 1,
                "type" : "track",
                "uri" : "spotify:track:1TKYPzH66GwsqyJFKFkBHQ"
                }, {
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
                },
            ],
            "seeds": [
                {
                "initialPoolSize": 500,
                "afterFilteringSize": 380,
                "afterRelinkingSize": 365,
                "href": "https://api.spotify.com/v1/artists/4NHQUGzhtTLFvgF5SZesLK",
                "id": "4NHQUGzhtTLFvgF5SZesLK",
                "type": "artist"
                }, {
                "initialPoolSize": 250,
                "afterFilteringSize": 172,
                "afterRelinkingSize": 144,
                "href": "https://api.spotify.com/v1/tracks/0c6xIDDpzE81m2q797ordA",
                "id": "0c6xIDDpzE81m2q797ordA",
                "type": "track"
                }
            ]
        }
        
        self.mock_refresh_token.return_value = '1234567890'
        self.mock_get_seeds.return_value = seeds
        self.mock_get_seed_names.return_value = [ "glam rock (genre)" , "Icona Pop (artist)", "permanent wave (genre)","All Night (song)"]
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = response

        result = {
            'seeds': [ "glam rock (genre)" , "Icona Pop (artist)", "permanent wave (genre)","All Night (song)"],
            'recommendations': [
                { 
                    'artists': ['134GdR5tUtxJrf8cpsfpyY', '1D2oK3cJRq97OXDzu77BFR'],
                    'explicit': False,
                    'id': '1TKYPzH66GwsqyJFKFkBHQ',
                    'name': 'Music Is Life'},
                {
                    'name': "All Night",
                    'id': "15iosIuxC3C53BgsM5Uggs",
                    'artists': [ '1VBflYyxBhnDc9uVib98rw' ],
                    'explicit': False,
                }
            ]
        }

        recommendations = playlist_generation.get_recommendations(intersection)

        self.assertDictEqual(result, recommendations)