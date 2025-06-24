# === dashboard.py (with Firebase write logs) ===
from fastapi import APIRouter, HTTPException, Header
from services.google_fit import google_fit_service
from services.spotify import spotify_service
from models.api_response import ApiResponse
from models.fitness import DashboardData
from database.session_manager import session_manager
import os

router = APIRouter()

@router.get("/")
async def get_dashboard_data(user_id: str = Header(..., alias="X-User-ID")):
    """Get dashboard data (live fetch from Google Fit + Spotify)"""
    try:
        session = session_manager.get_session(user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        step_data, heart_rate_data, sleep_data = [], [], []
        current_track = None
        recent_tracks = []
        spotify_connected = False

        if session.google_credentials:
            try:
                step_data, heart_rate_data, sleep_data, updated_credentials = await google_fit_service.get_fitness_data(
                    session.google_credentials, user_id=user_id
                )
                session_manager.update_session(user_id, google_credentials=updated_credentials)
            except Exception as e:
                print(f"Google Fit error: {e}")

        if session.spotify_token:
            spotify_connected = True
            access_token = session.spotify_token["access_token"]
            try:
                current_track = await spotify_service.get_current_track(access_token)
                recent_tracks = await spotify_service.get_recent_tracks(access_token)
                spotify_service.store_spotify_data(user_id, current_track.dict() if current_track else {}, [t.dict() for t in recent_tracks])
            except Exception as e:
                print(f"Spotify error: {e}")

        dashboard_data = DashboardData(
            step_data=step_data,
            heart_rate_data=heart_rate_data,
            sleep_data=sleep_data,
            current_track=current_track,
            recent_tracks=recent_tracks,
            spotify_connected=spotify_connected
        )

        return ApiResponse(success=True, message="Live dashboard fetched", data=dashboard_data.dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/firebase")
def get_dashboard_from_firebase(user_id: str = Header(..., alias="X-User-ID")):
    """Get dashboard data from stored Firebase cache (no re-fetch)"""
    try:
        session = session_manager.get_session(user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        step_data, heart_rate_data, sleep_data = google_fit_service.get_stored_google_fit_data(user_id)
        current_track, recent_tracks = spotify_service.get_stored_spotify_data(user_id)

        dashboard_data = DashboardData(
            step_data=step_data,
            heart_rate_data=heart_rate_data,
            sleep_data=sleep_data,
            current_track=current_track,
            recent_tracks=recent_tracks,
            spotify_connected=bool(session.spotify_token)
        )

        return ApiResponse(success=True, message="Dashboard data from Firebase", data=dashboard_data.dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-now")
async def sync_now(user_id: str = Header(..., alias="X-User-ID")):
    """Force sync latest Google Fit + Spotify data to Firebase"""
    try:
        session = session_manager.get_session(user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.google_credentials:
            try:
                steps, heart, sleep, updated = await google_fit_service.get_fitness_data(session.google_credentials, user_id)
                session_manager.update_session(user_id, google_credentials=updated)
                print(f"[Sync] Google Fit data synced for user {user_id}")
            except Exception as e:
                print(f"[Sync Error] Failed to sync Google Fit data for {user_id}: {e}")

        if session.spotify_token:
            try:
                token = session.spotify_token["access_token"]
                current = await spotify_service.get_current_track(token)
                recent = await spotify_service.get_recent_tracks(token)
                spotify_service.store_spotify_data(user_id, current.dict() if current else {}, [r.dict() for r in recent])
                print(f"[Sync] Spotify data synced for user {user_id}")
            except Exception as e:
                print(f"[Sync Error] Failed to sync Spotify data for {user_id}: {e}")

        return ApiResponse(success=True, message="Data synced to Firebase", data=None)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
