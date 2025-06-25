import base64
from typing import Optional, List
import httpx
from models.fitness import SpotifyTrack

class SpotifyService:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = 'http://127.0.0.1:5000/spotify/callback'
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
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
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