"""
Name: app.py
Description: Flask code for a website. Assists with displaying user's top
             Spotify stats and creating playlists with top songs.
Author: @shahhh-z on GitHub
"""

# Import libraries.
from flask import Flask, redirect, request, url_for, render_template, session
import requests
import secrets
import os
from dotenv import load_dotenv


# Load in the sensitive information.
load_dotenv()


# Create the flask app.
app = Flask(__name__)


# Create the secret key.
app.secret_key = secrets.token_hex(24)


# Set the variables equal to the sensitive information.
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


"""
refreshToken: Refreshes the access token without prompting the user to sign
              into Spotify again.
"""
def refreshToken():
    # Get the refresh token.
    refresh_token = session.get('refresh_token')
    if (not refresh_token):
        return None
    
    # Request a new access token.
    response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    })
    responseData = response.json()
    
    # Get the new access token.
    new_access_token = responseData.get('access_token')
    if (new_access_token):
        session['access_token'] = new_access_token
    
    # Return the new access token.
    return new_access_token


"""
getResponse: Takes a url and it performs a call to Spotify's API. Returns the
             response from the API.
"""
def getResponse(url):
    # Make an API call using the url and headers.
    headers = {
            'Authorization': f"Bearer {session.get('access_token')}",
            'Content-Type': 'application/json'
        }
    response = requests.get(url, headers=headers)
    
    if (response.status_code == 401):
        # Refresh the access token and try again if the token is expired.
        access_token = refreshToken()
        if (access_token):
            headers['Authorization'] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)
            return response
        else:
            # Return nothing if the token could not be refreshed.
            print("Failed to refresh token")
            return None
    # Return the response of the API call.
    return response


"""
postResponse: Takes a url and data. Performs a call to Spotify's API. Returns
              the response from the API.
"""
def postResponse(url, data):
    # Make an API call using the url, headers, and data.
    headers = {
            'Authorization': f"Bearer {session.get('access_token')}",
            'Content-Type': 'application/json'
        }
    response = requests.post(url, headers=headers, json=data)
    
    if (response.status_code == 401):
        # Refresh the access token and try again if the token is expired.
        access_token = refreshToken()
        if (access_token):
            headers['Authorization'] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)
            return response
        else:
            # Return nothing if the token could not be refreshed.
            print("Failed to refresh token")
            return None
    # Return the response of the API call.
    return response


"""
getUserID: Gets the user's Spotify ID (if it has not been accessed yet) and
           returns it.
"""
def getUserID():
    # Get the user's ID.
    userID = session.get('userID')
    if (not userID):
        userData = getResponse("https://api.spotify.com/v1/me").json()
        userID = userData.get("id", None)
    # Return the user's ID or nothing if it could not be retrieved.
    return userID


"""
getSongs: Takes the given time range and returns the response of the API call
          for the top songs of the time range.
"""
def getSongs(timeRange):
    # Make an API call for the user's top songs with the time range given.
    response = getResponse(f"https://api.spotify.com/v1/me/top/tracks?time_range={timeRange}&limit=50")
    if (response == None):
        # Return an empty list if the response is nothing.
        return []
    else:
        # Return the list of top songs.
        responseData = response.json()
        topSongs = responseData.get("items", [])
        return topSongs


"""
getArtists: Takes the given time range and returns the response of the API
            call for the top artists of the time range.
"""
def getArtists(timeRange):
    # Make an API call for the user's top artists with the time range given.
    response = getResponse(f"https://api.spotify.com/v1/me/top/artists?time_range={timeRange}&limit=50")
    if (response == None):
        # Return an empty list if the response is nothing.
        return []
    else:
        # Return the list of top artists.
        responseData = response.json()
        topArtists = responseData.get("items", [])
        return topArtists


"""
index: Displays the login page.
"""
@app.route('/')
def index():
    return render_template("index.html")


"""
login: Prompts the user to sign in.
"""
@app.route('/login')
def login():
    # Get the referrer URL
    session['referrerURL'] = request.args.get('next') or url_for('index')
    return redirect(f'https://accounts.spotify.com/authorize?response_type=code&client_id={SPOTIFY_CLIENT_ID}&scope=user-library-read%20user-read-private%20user-top-read%20playlist-modify-private%20user-read-email%20playlist-modify-public&redirect_uri={REDIRECT_URI}')


"""
callback: Gets the user's access token and refresh token. Returns to the page
          that the login function was called from.
"""
@app.route('/callback')
def callback():
    # Get the access token and the refresh token.
    code = request.args.get('code')
    response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    })
    responseData = response.json()
    session['access_token'] = responseData.get('access_token')
    session['refresh_token'] = responseData.get('refresh_token')

    # Go to the referrer URL.
    referrerURL = session.pop('referrerURL', url_for('home'))
    if (referrerURL == '/'):
        referrerURL = url_for('home')
    return redirect(referrerURL)


"""
home: Displays the home page.
"""
@app.route('/home')
def home():
    return render_template("home.html")


"""
stats: Displays the top stats for the given time range.
"""
@app.route('/stats')
def stats():
    # Get the access token.
    access_token = session.get('access_token')
    if (not access_token):
        return redirect(url_for('login', next=url_for('stats')))
    
    # Get the time range.
    timeRange = request.args.get('timeRange', 'short_term')
    
    # Create a dictionary with the info for each artist and song.
    songsWithInfo = {song.get("id", None): {'image': song.get("album", {}).get("images", [{}])[0].get("url", None), 'name': song.get("name", None)} for song in getSongs(timeRange)}
    artistsWithInfo = {artist.get("id", None): {'image': artist.get("images", [{}])[0].get("url", None), 'name': artist.get("name", None)} for artist in getArtists(timeRange)}

    # Display the stats page with the song and artist dictionaries.
    return render_template(
        "stats.html",
        top_songs=songsWithInfo,
        top_artists=artistsWithInfo
    )


"""
playlist: Gets the message and displays the playlist page.
"""
@app.route('/playlist')
def playlist():
    message = request.args.get('message', '')
    return render_template("playlist.html", message=message)


"""
submit: Creates a Spotify playlist of top songs based on the form input.
"""
@app.route('/submit', methods=['POST'])
def submit():
    # Get the time range.
    timeRange = request.form.get('timeRange', 'short_term')

    # Get the description for the playlist.
    description = ""
    match (timeRange):
        case "long_term":
            description = "year"
        case "medium_term":
            description = "6 months"
        case "short_term":
            description = "4 weeks"
    
    # Create the playlist.
    playlistData = {
    'name': f"Your Top Songs ({description})",
    'description': f"Your top songs of the past {description}!",
    'public': False
    }
    newPlaylist = postResponse(f"https://api.spotify.com/v1/users/{getUserID()}/playlists", playlistData).json()

    # Get the playlist ID.
    playlistID = newPlaylist.get("id", None)

    songList = []
    if (playlistID != None):
        # Add each of the top songs's URIs to the list.
        for song in getSongs(timeRange):
            songList.append(song.get("uri", None))
        # Add the songs to the playlist.
        postResponse(f"https://api.spotify.com/v1/playlists/{playlistID}/tracks", {'uris': songList, 'position': 0})
        # Change the message to let the user know that the playlist was made.
        message = "Playlist Created"
    else:
        # Change the message if the playlist creation failed.
        message = "Playlist Creation Failed"
    
    # Display the playlist page with the new message.
    return redirect(url_for("playlist", message=message))


"""
logout: Pop the info stored in session and display the login page.
"""
@app.route('/logout')
def logout():
    session.pop('userID', None)
    session.pop('refresh_token', None)
    session.pop('access_token', None)
    return redirect(url_for('index'))