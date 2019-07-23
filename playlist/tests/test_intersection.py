from unittest.mock import Mock, patch
from unittest import TestCase
from playlist import intersection

# Mock API data from Spotify API Docs :
# https://developer.spotify.com/documentation/web-api/reference/


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
        common_artists = intersection.find_common_artists(self.user1, self.user2)
        for artist_id in result:
            self.assertIn(artist_id, common_artists)
        self.assertCountEqual(result, common_artists)

    def test_find_common_songs(self):
        result = ["15iosIuxC3C53BgsM5Uggs"]
        common_songs = intersection.find_common_songs(self.user1, self.user2)
        for artist_id in result:
            self.assertIn(artist_id, common_songs)
        self.assertCountEqual(result, common_songs)

    def test_find_common_genres(self):
        result = ["swedish hip hop", "art rock", "glam rock", "permanent wave"]
        common_genres = intersection.find_common_genres(self.user1, self.user2)
        for genre in result:
            self.assertIn(genre, common_genres)
        self.assertCountEqual(result, common_genres)
