from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from services.google_fit import google_fit_service
from services.spotify import SpotifyService
from database.mental_health_db import mental_health_db
import os
from typing import Dict, Any

router = APIRouter()

# Initialize Spotify service with credentials from environment
spotify_service = SpotifyService(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
)

def get_current_user_id(request: Request) -> str:
    """Fetch current user ID from session"""
    if 'credentials' not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.session['credentials'].get('client_id', 'default_user')


async def get_fitness_data(request: Request) -> tuple:
    try:
        print("🟢 Fetching fitness data...")
        step_data, heart_rate_data, sleep_data, calories_data, updated_credentials = await google_fit_service.get_fitness_data(
            request.session['credentials']
        )
        request.session['credentials'] = updated_credentials
        return step_data, heart_rate_data, sleep_data, calories_data
    except Exception as e:
        print(f"❌ Error fetching fitness data: {str(e)}")
        return [], [], [], []


async def get_spotify_data(request: Request) -> tuple:
    spotify_connected = False
    current_track = None
    recent_tracks = []
    audio_summary = {}

    try:
        user_id = get_current_user_id(request)
        token_info = request.session.get(f'spotify_token_{user_id}')
        spotify_connected = bool(token_info)

        if spotify_connected:
            access_token = token_info['access_token']
            current_track = await spotify_service.get_current_track(access_token)
            recent_tracks, audio_summary = await spotify_service.get_recent_tracks_with_features(access_token)

            print("🟢 Spotify data fetched")
    except Exception as e:
        print(f"❌ Error fetching Spotify data: {str(e)}")
        request.session.pop(f'spotify_token_{user_id}', None)
        spotify_connected = False

    return spotify_connected, current_track, recent_tracks, audio_summary


async def get_mental_health_data(request: Request) -> Dict[str, Any]:
    try:
        user_id = get_current_user_id(request)
        return mental_health_db.get_user_data(user_id)
    except Exception as e:
        print(f"❌ Error fetching mental health data: {str(e)}")
        return {'conditions': [], 'medications': []}


@router.get("/api/dashboard")
async def dashboard_api(request: Request):
    """Main API route for Android app to fetch all dashboard data"""
    if 'credentials' not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Fetch Google Fit, Spotify, Mental Health
        step_data, heart_rate_data, sleep_data, calories_data = await get_fitness_data(request)
        spotify_connected, current_track, recent_tracks, audio_summary = await get_spotify_data(request)
        mental_health_data = await get_mental_health_data(request)

        return {
            "step_data": step_data,
            "heart_rate_data": heart_rate_data,
            "sleep_data": sleep_data,
            "calories_data": calories_data,
            "spotify_connected": spotify_connected,
            "current_track": current_track,
            "recent_tracks": recent_tracks,
            "audio_summary": audio_summary,
            "mental_health": mental_health_data
        }

    except Exception as e:
        print(f"❌ Error in /api/dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

