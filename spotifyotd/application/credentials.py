from dotenv import load_dotenv, find_dotenv
import os
import pprint
load_dotenv(find_dotenv())

connection_string = os.environ.get('connection_string')

client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')

redirect_uri = 'http://127.0.0.1:8000/onthisday/'
auth_url = 'https://accounts.spotify.com/authorize'
token_url = 'https://accounts.spotify.com/api/token'
lib_url = 'https://api.spotify.com/v1/me/tracks/'
aud_url = 'https://api.spotify.com/v1/audio-features/'
usr_url = 'https://api.spotify.com/v1/me/'
spot_url ='https://api.spotify.com/v1/users/spotify/playlists'