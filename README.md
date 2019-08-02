## Playlist for Two

Playlist for Two is a social music discovery app integrated with Spotify that enables users to generate playlists based on common songs, artists, and genres using Spotify's recommendation engine. The back end for the app was built with Flask and MongoDB and deployed on Heroku. The [mobile client](https://github.com/shubha-rajan/playlist-for-two-frontend/) for the app is cross-platform (ios/Android) and was built using [Flutter](https://flutter.dev/)

Playlist for Two was developed by Shubha Rajan as a capstone project for [Ada Developers' Academy](https://adadevelopersacademy.org).

## Getting Started

Requirements to try it out:

- A [Spotify](spotify.com) account with a lengthy listening history or number of saved songs and followed artists.
- A mobile phone or emulator.
- A friend who also has both of the above!

## For Developers

- Clone this repo.
- Create a [Spotify Developer](https://developer.spotify.com/dashboard/) account and make an app to get a client ID and client secret (if you haven't already)
- Set the following environment variables, either with a .env file or `heroku config:set` (or similar):
```
SPOTIFY_CLIENT_ID={Your client ID}
 
SPOTIFY_CLIENT_SECRET={Your client secret}

SPOTIFY_USER_ID={Your user ID, this will be the ID of the account used to generate playlists} 

JWT_SECRET= {any cryptographically secure random string}

MONGODB_URI={ the uri to connect to your database }
```
- Get a Spotify Refresh token for the account you're using to generate playlists. The scopes needed are `playlist-read-private` and `playlist-modify-private` (Walkthrough using postman can be found [here](https://documenter.getpostman.com/view/583/spotify-playlist-generator/2MtDWP?version=latest)
- In your MongoDB console, add a new User document using 
`db.user.insertOne({name: "Playlist for Two", id: {your user id}, sp_access_token: {your access token} , sp_refresh_token:{your refresh token})`
- Run your server, if running locally
- Make sure the [Mobile Client](https://github.com/shubha-rajan/playlist-for-two-frontend/) is set up and run the app from a phone.
