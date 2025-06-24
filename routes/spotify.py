import uuid
import os
from fastapi import APIRouter, HTTPException, Header
from services.spotify import SpotifyService
from models.auth import SpotifyAuthRequest, SpotifyAuthResponse
from models.api_response import ApiResponse
from database.session_manager import session_manager

router = APIRouter()

# Initialize Spotify service with mobile redirect URI
spotify_service = SpotifyService(
    client_id=os.getenv("5bc3a32f5662485586dd111be225164b"),
    client_secret=os.getenv("09052b4c6cb3482db6c783d9e9dc6c87"),
    redirect_uri='com.yourapp.healthmusic://callback'  # Mobile custom scheme
)

@router.get("/authorize-url")
async def get_spotify_auth_url():
    """Get Spotify OAuth authorization URL for mobile app"""
    try:
        state = str(uuid.uuid4())
        auth_url = spotify_service.get_auth_url(state)
        
        return ApiResponse(
            success=True,
            message="Spotify authorization URL generated successfully",
            data={
                "auth_url": auth_url,
                "state": state,
                "redirect_uri": spotify_service.redirect_uri
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Spotify auth URL: {str(e)}")

@router.post("/exchange-token")
async def exchange_spotify_token(
    auth_request: SpotifyAuthRequest,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Exchange Spotify authorization code for access token"""
    try:
        token_data = await spotify_service.exchange_code_for_token(auth_request.code)
        
        # Update user session with Spotify token
        session_manager.update_session(user_id, spotify_token=token_data)
        
        return SpotifyAuthResponse(
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            expires_in=token_data['expires_in']
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Spotify token exchange failed: {str(e)}")

@router.get("/current-track")
async def get_current_track(user_id: str = Header(..., alias="X-User-ID")):
    """Get currently playing Spotify track"""
    try:
        session = session_manager.get_session(user_id)
        if not session or not session.spotify_token:
            raise HTTPException(status_code=401, detail="Spotify not connected")
        
        access_token = session.spotify_token['access_token']
        current_track = await spotify_service.get_current_track(access_token)
        
        return ApiResponse(
            success=True,
            message="Current track retrieved successfully",
            data=current_track.dict() if current_track else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current track: {str(e)}")

@router.get("/recent-tracks")
async def get_recent_tracks(
    user_id: str = Header(..., alias="X-User-ID"),
    limit: int = 10
):
    """Get recently played Spotify tracks"""
    try:
        session = session_manager.get_session(user_id)
        if not session or not session.spotify_token:
            raise HTTPException(status_code=401, detail="Spotify not connected")
        
        access_token = session.spotify_token['access_token']
        recent_tracks = await spotify_service.get_recent_tracks(access_token, limit)
        
        return ApiResponse(
            success=True,
            message="Recent tracks retrieved successfully",
            data=[track.dict() for track in recent_tracks]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent tracks: {str(e)}")
