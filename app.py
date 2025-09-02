import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import time

# --- Environment Variables & Constants ---
# For security, it's best to set these as environment variables.
# You can also hardcode them for local testing, but this is not recommended for deployment.
CLIENT_ID = st.secrets["SPOTIPY_CLIENT_ID"]
CLIENT_SECRET = st.secrets["SPOTIPY_CLIENT_SECRET"]
# The redirect URI must match the one set in your Spotify Developer Dashboard.
# For local development, `http://localhost:8501` is common.
REDIRECT_URI = st.secrets["SPOTIPY_REDIRECT_URI"]

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Spotify Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Helper Functions ---

def get_spotify_oauth():
    """Creates and returns a SpotifyOAuth object for authentication."""
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="user-read-private user-read-email user-top-read user-read-recently-played",
        cache_path=".spotifycache" # Caches tokens
    )

def get_token_info():
    """
    Retrieves token information from the session state.
    Handles the authorization code flow if a code is present in the URL.
    """
    # Check if the auth code is in the URL query params
    if 'code' in st.query_params:
        auth_code = st.query_params['code']
        sp_oauth = get_spotify_oauth()
        try:
            # Exchange the auth code for an access token
            token_info = sp_oauth.get_access_token(auth_code, as_dict=True)
            st.session_state['token_info'] = token_info
            # Clear the query params to prevent re-using the code
            st.query_params.clear()
            st.rerun() # Rerun to update the state
        except Exception as e:
            st.error(f"Error getting access token: {e}")
            return None
    # If token info is already in the session, return it
    return st.session_state.get('token_info', None)

def get_spotify_client(token_info):
    """
    Creates and returns an authenticated Spotipy client.
    Handles token refreshing automatically.
    """
    if not token_info:
        return None

    sp_oauth = get_spotify_oauth()

    # Check if the token is expired and refresh if necessary
    now = int(time.time())
    is_expired = token_info.get('expires_at', 0) - now < 60
    if is_expired:
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            st.session_state['token_info'] = token_info
        except Exception as e:
            st.error(f"Error refreshing access token: {e}")
            # If refresh fails, force re-login
            st.session_state.pop('token_info', None)
            return None

    return spotipy.Spotify(auth=token_info['access_token'])


def display_user_profile(sp):
    """Displays the user's Spotify profile information."""
    user = sp.current_user()
    col1, col2 = st.columns([1, 4])
    with col1:
        if user['images']:
            st.image(user['images'][0]['url'], width=150)
        else:
            st.image("https://placehold.co/150x150/2c2c2c/ffffff?text=User", width=150)
    with col2:
        st.title(f"Welcome, {user['display_name']}!")
        st.subheader(f"Email: {user['email']}")
        st.write(f"Followers: {user['followers']['total']}")
        st.link_button("View Profile on Spotify", user['external_urls']['spotify'])

def display_top_artists(sp):
    """Displays the user's top artists."""
    st.header("Your Top Artists (Last 6 Months)")
    top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')
    if not top_artists['items']:
        st.warning("Couldn't find any top artists. Go listen to some music!")
        return

    cols = st.columns(5)
    for i, artist in enumerate(top_artists['items']):
        with cols[i % 5]:
            with st.container(border=True):
                if artist['images']:
                    st.image(artist['images'][2]['url'])
                st.markdown(f"**{i+1}. {artist['name']}**")
                st.markdown(f"*{', '.join(g.title() for g in artist['genres'][:2])}*")
                st.link_button("Listen", artist['external_urls']['spotify'], use_container_width=True)


def display_recently_played(sp):
    """Displays recently played tracks."""
    st.header("Recently Played Tracks")
    recently_played = sp.current_user_recently_played(limit=10)
    if not recently_played['items']:
        st.warning("No recently played tracks found.")
        return

    for item in recently_played['items']:
        track = item['track']
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(track['album']['images'][0]['url'], width=80)
        with col2:
            st.markdown(f"**{track['name']}**")
            st.markdown(f"By {track['artists'][0]['name']} on *{track['album']['name']}*")
            st.link_button("Play on Spotify", track['external_urls']['spotify'])
        st.divider()

# --- Main App Logic ---
def main():
    """Main function to run the Streamlit app."""
    # Check for missing credentials
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        st.error("🚨 Critical Error: Spotify API credentials are not set.")
        st.info("Please set SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI as environment variables.")
        st.info("Refer to the README.md file for instructions.")
        st.stop()

    token_info = get_token_info()

    if not token_info:
        # --- LOGIN PAGE ---
        st.title("🎵 Your Personal Spotify Dashboard")
        st.write("Log in to see your listening habits and stats.")

        sp_oauth = get_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        # Use st.link_button for a clean, non-form based redirection
        st.link_button("Login with Spotify", auth_url, use_container_width=True)
    else:
        # --- LOGGED-IN DASHBOARD ---
        sp = get_spotify_client(token_info)

        if sp:
            # --- Sidebar for Logout ---
            with st.sidebar:
                st.header("Controls")
                if st.button("Logout"):
                    st.session_state.pop('token_info', None)
                    st.rerun()

            # --- Main Content ---
            display_user_profile(sp)
            st.divider()
            display_top_artists(sp)
            st.divider()
            display_recently_played(sp)
        else:
            # Handle case where client could not be created (e.g., token refresh failed)
            st.error("Could not connect to Spotify. Please try logging in again.")
            if st.button("Retry Login"):
                 st.session_state.pop('token_info', None)
                 st.rerun()


if __name__ == "__main__":
    main()
