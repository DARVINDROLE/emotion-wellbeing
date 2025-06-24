# models/auth.py
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class AuthTokenRequest(BaseModel):
    code: str
    state: str

class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    user_id: str

class SpotifyAuthRequest(BaseModel):
    code: str
    state: str

class SpotifyAuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int

class UserSession(BaseModel):
    user_id: str
    google_credentials: Optional[Dict] = None
    spotify_token: Optional[Dict] = None
    created_at: str