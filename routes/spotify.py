import uuid
import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from services.spotify import SpotifyService

router = APIRouter()

# Initialize Spotify service
spotify_service = SpotifyService(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
)

@router.get("/authorize")
async def spotify_authorize(request: Request):
    state = str(uuid.uuid4())
    request.session['spotify_state'] = state
    
    auth_url = spotify_service.get_auth_url(state)
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def spotify_callback(request: Request):
    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if state != request.session.get('spotify_state'):
        raise HTTPException(status_code=400, detail="Invalid Spotify state")

    try:
        token_data = await spotify_service.exchange_code_for_token(code)
        request.session['spotify_token'] = token_data
        return RedirectResponse(url="/dashboard")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to authenticate with Spotify: {str(e)}")

@router.get("/dashboard")
async def spotify_dashboard():
    # Redirect to main dashboard
    return RedirectResponse(url="/dashboard")