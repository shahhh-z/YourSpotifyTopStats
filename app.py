from flask import Flask, redirect, request, url_for, render_template, session
import requests
# import ranker
import secrets
# from flask_caching import Cache

app = Flask(__name__)
# cache_config = {
#     'CACHE_TYPE': 'simple',  # Simple in-memory cache
#     'CACHE_DEFAULT_TIMEOUT': 300  # Cache timeout in seconds
# }
# cache = Cache(app, config=cache_config)

app.secret_key = secrets.token_hex(24)

SPOTIFY_CLIENT_ID="20ccae3222544f199e51184a6f3795f3"
SPOTIFY_CLIENT_SECRET="dc46b212e0854d6587104445731fc962"
REDIRECT_URI="https://shahhhz.pythonanywhere.com/callback"

# # Initialize ranking objects
# topMusicStats = ranker.musicRankings()
topSongs = []
userID = ""

def refreshToken():
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        return None
    
    response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    })
    response_data = response.json()
    
    new_access_token = response_data.get('access_token')
    if new_access_token:
        session['access_token'] = new_access_token
    
    return new_access_token

def getResponse(url):
    headers = {
            'Authorization': f"Bearer {session.get('access_token')}",
            'Content-Type': 'application/json'
        }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:  # Token might be expired
        access_token = refreshToken()
        if access_token:
            headers['Authorization'] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)
            return response
        else:
            print("Failed to refresh token")
            return None
    return response

def postResponse(url, data):
    headers = {
            'Authorization': f"Bearer {session.get('access_token')}",
            'Content-Type': 'application/json'
        }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 401:  # Token might be expired
        access_token = refreshToken()
        if access_token:
            headers['Authorization'] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)
            return response
        else:
            print("Failed to refresh token")
            return None
    return response

def getUserID():
    global userID
    if (userID == ""):
        userData = getResponse("https://api.spotify.com/v1/me").json()
        userID = userData.get("id", None)
    return userID

def get_songs(timeRange):
    response = getResponse(f"https://api.spotify.com/v1/me/top/tracks?time_range={timeRange}&limit=50")
    if (response == None):
        return []
    else:
        topSongs = []
        response_data = response.json()
        for song in response_data.get("items", []):
            topSongs.append(song)
        return topSongs

def get_artists(timeRange):
    response = getResponse(f"https://api.spotify.com/v1/me/top/artists?time_range={timeRange}&limit=50")
    if (response == None):
        return []
    else:
        topArtists = []
        response_data = response.json()
        for artist in response_data.get("items", []):
            topArtists.append(artist)
        return topArtists

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    session['referrer_url'] = request.args.get('next') or url_for('index')
    return redirect(f'https://accounts.spotify.com/authorize?response_type=code&client_id={SPOTIFY_CLIENT_ID}&scope=user-library-read%20user-read-private%20user-top-read%20playlist-modify-private%20user-read-email%20playlist-modify-public&redirect_uri={REDIRECT_URI}')

@app.route('/callback')
def callback():
    code = request.args.get('code')
    response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    })
    response_data = response.json()
    session['access_token'] = response_data.get('access_token')
    session['refresh_token'] = response_data.get('refresh_token')
    referrer_url = session.pop('referrer_url', url_for('home'))

    if (referrer_url == '/'):
        referrer_url = url_for('home')
    
    return redirect(referrer_url)

# @app.route('/profile')
# def profile():
#     access_token = session.get('access_token')
#     headers = {'Authorization': f'Bearer {access_token}'}
#     response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers)
#     data = response.json()
    
#     # Process and update rankings
#     for track_data in data['items']:
#         song = track.Song(
#             time=track_data['added_at'],
#             track=track_data['name'],
#             artists=[artist['name'] for artist in track_data['artists']],
#             album=track_data['album']['name'],
#             uri=track_data['uri']
#         )
#         # Update ranking data
#         topMusicStats.updSong(song, secondsPlayed=0, timestamp=track_data['added_at'])
    
#     return jsonify(topMusicStats.getTopSongs())

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/stats')
# @cache.cached(timeout=500)
def stats():
    access_token = session.get('access_token')
    
    if not access_token:
        return redirect(url_for('login', next=url_for('stats')))
    
    timeRange = request.args.get('timeRange', 'short_term')

    try:
        # Check if the access token is expired
        response = requests.get("https://api.spotify.com/v1/me", headers={'Authorization': f'Bearer {access_token}'})
        if response.status_code == 401:  # Unauthorized, possibly expired token
            access_token = refreshToken()
            if not access_token:
                return redirect(url_for('login'))
    except requests.RequestException as e:
        print(f"Error during token refresh: {e}")
        return redirect(url_for('login'))

    # # Get the top 50 songs, albums, and artists
    # start_date = 20240101  # Example start date
    # end_date = 20240826    # Example end date

    # top_songs = topMusicStats.songRanks(start_date, end_date)
    # top_albums = topMusicStats.albumRanks(start_date, end_date)
    # top_artists = topMusicStats.artistRanks(start_date, end_date)

    # def get_song_info(song_uri):
    #     headers = {
    #         'Authorization': f"Bearer {session.get('access_token')}",
    #         'Content-Type': 'application/json'
    #     }
    #     response = requests.get(f"https://api.spotify.com/v1/tracks/{song_uri}", headers=headers)
    #     if response.status_code == 401:  # Token might be expired
    #         access_token = refreshToken()
    #         if access_token:
    #             headers['Authorization'] = f"Bearer {access_token}"
    #             response = requests.get(f"https://api.spotify.com/v1/tracks/{song_uri}", headers=headers)
    #         else:
    #             print("Failed to refresh token")
    #             return None

    #     response_data = response.json()
    #     return [response_data.get('album', {}).get('images', [{}])[0].get('url', None), response_data.get('name', None)]

    # def get_album_info(album_uri):
    #     headers = {
    #         'Authorization': f"Bearer {session.get('access_token')}",
    #         'Content-Type': 'application/json'
    #     }
    #     response = requests.get(f"https://api.spotify.com/v1/albums/{album_uri}", headers=headers)
    #     if response.status_code == 401:  # Token might be expired
    #         access_token = refreshToken()
    #         if access_token:
    #             headers['Authorization'] = f"Bearer {access_token}"
    #             response = requests.get(f"https://api.spotify.com/v1/albums/{album_uri}", headers=headers)
    #         else:
    #             print("Failed to refresh token")
    #             return None

    #     response_data = response.json()
    #     return [response_data.get('images', [{}])[0].get('url', None), response_data.get('name', None)]

    # def get_artist_info(artist_uri):
    #     headers = {
    #         'Authorization': f"Bearer {session.get('access_token')}",
    #         'Content-Type': 'application/json'
    #     }
    #     response = requests.get(f"https://api.spotify.com/v1/artists/{artist_uri}", headers=headers)
    #     if response.status_code == 401:  # Token might be expired
    #         access_token = refreshToken()
    #         if access_token:
    #             headers['Authorization'] = f"Bearer {access_token}"
    #             response = requests.get(f"https://api.spotify.com/v1/artists/{artist_uri}", headers=headers)
    #         else:
    #             print("Failed to refresh token")
    #             return None

    #     response_data = response.json()
    #     return [response_data.get('images', [{}])[0].get('url', None), response_data.get('name', None)]

    
    # songs_with_images = {song: {'image': get_song_info(song)[0], 'name': get_song_info(song)[1], 'data': data} for song, data in top_songs.items()}
    # songs_with_images = {song: {'image': get_song_info(song)[0], 'name': get_song_info(song)[1]} for song in topSongs}
    songs_with_images = {song.get("id", None): {'image': song.get("album", {}).get("images", [{}])[0].get("url", None), 'name': song.get("name", None)} for song in get_songs(timeRange)}
    # artists_with_images = {artist: {'image': get_artist_info(artist)[0], 'name': get_artist_info(artist)[1]} for artist in get_artists()}
    artists_with_images = {artist.get("id", None): {'image': artist.get("images", [{}])[0].get("url", None), 'name': artist.get("name", None)} for artist in get_artists(timeRange)}
    # albums_with_images = {album: {'image': get_album_info(album)[0], 'name': get_album_info(album)[1], 'data': data} for album, data in top_albums.items()}
    # artists_with_images = {artist: {'image': get_artist_info(artist)[0], 'name': get_artist_info(artist)[1], 'data': data} for artist, data in top_artists.items()}

    return render_template(
        "stats.html",
        top_songs=songs_with_images,
        # top_albums=albums_with_images,
        top_artists=artists_with_images
    )

@app.route('/playlist')
def playlist():
    message = request.args.get('message', '')
    return render_template("playlist.html", message=message)

@app.route('/submit', methods=['POST'])
def submit():
    timeRange = request.form.get('timeRange', 'short_term')  # Get the value from the dropdown

    description = ""
    match (timeRange):
        case "long_term":
            description = "year"
        case "medium_term":
            description = "6 months"
        case "short_term":
            description = "4 weeks"

    playlistData = {
    'name': f"Your Top Songs ({description})",
    'description': f"Your top songs of the past {description}!",
    'public': False
    }
    playlst = postResponse(f"https://api.spotify.com/v1/users/{getUserID()}/playlists", playlistData).json()
    playlistID = playlst.get("id", None)
    songList = []

    if (playlistID != None):
        for song in get_songs(timeRange):
            songList.append(song.get("uri", None))
        postResponse(f"https://api.spotify.com/v1/playlists/{playlistID}/tracks", {'uris': songList, 'position': 0})
        message = "Playlist Created"
    else:
        message = "Playlist Creation Failed"

    return redirect(url_for("playlist", message=message))

# @app.route('/import')
# def importStats():
#     return render_template("import.html")
