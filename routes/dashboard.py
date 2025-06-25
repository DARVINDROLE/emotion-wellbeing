from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.google_fit import google_fit_service
from services.spotify import SpotifyService
from database.mental_health_db import mental_health_db
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Initialize Spotify service
spotify_service = SpotifyService(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
)

def get_current_user_id(request: Request) -> str:
    """Get current user ID from session"""
    if 'credentials' not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.session['credentials'].get('client_id', 'default_user')

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if 'credentials' not in request.session:
        return RedirectResponse(url="/authorize")

    # Get Google Fit data
    try:
        step_data, heart_rate_data, sleep_data, updated_credentials = await google_fit_service.get_fitness_data(
            request.session['credentials']
        )
        # Update session with refreshed credentials if needed
        request.session['credentials'] = updated_credentials
    except Exception as e:
        print(f"Error fetching fitness data: {e}")
        step_data, heart_rate_data, sleep_data = [], [], []

    # Get Spotify data
    current_track = None
    recent_tracks = []
    spotify_connected = False
    
    token_info = request.session.get('spotify_token')
    if token_info:
        spotify_connected = True
        access_token = token_info['access_token']
        
        try:
            current_track = await spotify_service.get_current_track(access_token)
            recent_tracks = await spotify_service.get_recent_tracks(access_token)
        except Exception as e:
            print(f"Error fetching Spotify data: {e}")

    # Get mental health data
    user_id = get_current_user_id(request)
    mental_health_data = mental_health_db.get_user_data(user_id)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "step_data": step_data,
        "heart_rate_data": heart_rate_data,
        "sleep_data": sleep_data,
        "current_track": current_track,
        "recent_tracks": recent_tracks,
        "spotify_connected": spotify_connected,
        "mental_health": mental_health_data
    })
