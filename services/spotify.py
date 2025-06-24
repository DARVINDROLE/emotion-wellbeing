# === spotify.py (with Firebase logging) ===
import base64
from typing import Optional, List
import httpx
from models.fitness import SpotifyTrack
from services.firebase import db

class SpotifyService:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri or 'com.yourapp.healthmusic://callback'
        self.scopes = "user-read-playback-state user-read-recently-played"

    def get_auth_url(self, state: str) -> str:
        from urllib.parse import urlencode
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': self.scopes,
            'state': state
        }
        return f"https://accounts.spotify.com/authorize?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict:
        token_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
        }

        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to exchange code for token: {response.text}")

        return response.json()

    async def get_current_track(self, access_token: str) -> Optional[SpotifyTrack]:
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.spotify.com/v1/me/player/currently-playing',
                    headers=headers
                )

            if response.status_code == 200:
                data = response.json()
                if data and data.get("item"):
                    return SpotifyTrack(
                        name=data["item"]["name"],
                        artist=data["item"]["artists"][0]["name"],
                        album=data["item"]["album"]["name"],
                        image=data["item"]["album"]["images"][0]["url"] if data["item"]["album"]["images"] else None
                    )
        except Exception as e:
            print(f"Error fetching current track: {e}")

        return None

    async def get_recent_tracks(self, access_token: str, limit: int = 5) -> List[SpotifyTrack]:
        headers = {'Authorization': f'Bearer {access_token}'}
        tracks = []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://api.spotify.com/v1/me/player/recently-played?limit={limit}',
                    headers=headers
                )

            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    track = item["track"]
                    tracks.append(SpotifyTrack(
                        name=track["name"],
                        artist=track["artists"][0]["name"],
                        played_at=item["played_at"],
                        image=track["album"]["images"][0]["url"] if track["album"]["images"] else None
                    ))
        except Exception as e:
            print(f"Error fetching recent tracks: {e}")

        return tracks

    def store_spotify_data(self, user_id: str, current_track: dict, recent_tracks: list):
        try:
            user_ref = db.collection("users").document(user_id).collection("spotify")
            user_ref.document("current_track").set(current_track)
            user_ref.document("recent_tracks").set({"tracks": recent_tracks})
            print(f"[Firebase] Stored current + {len(recent_tracks)} recent tracks for user {user_id}")
        except Exception as e:
            print(f"[Firebase Error] Failed to store Spotify data for user {user_id}: {e}")

    def get_stored_spotify_data(self, user_id: str):
        spotify_ref = db.collection("users").document(user_id).collection("spotify")
        current = spotify_ref.document("current_track").get().to_dict()
        recent = spotify_ref.document("recent_tracks").get().to_dict()
        return current, recent.get("tracks", []) if recent else []

spotify_service = SpotifyService
