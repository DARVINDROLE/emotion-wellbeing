import os
import uuid
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from google_auth_oauthlib.flow import Flow
from typing import Optional
from models.auth import AuthTokenRequest, AuthTokenResponse, UserSession
from models.api_response import ApiResponse
from database.session_manager import session_manager


router = APIRouter()

CLIENT_SECRETS_FILE = "client_secret.json"
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]
# Mobile redirect URI - you'll need to update this
REDIRECT_URI = 'com.yourapp.healthmusic://oauth/google'  # Custom scheme for mobile
@router.get("/callback")
async def callback(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=f"OAuth error: {request.query_params.get('error')}")

    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if not code:
        raise HTTPException(status_code=400, detail="No code received from Google")

    # optional: validate state (if you're storing it in session)

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=GOOGLE_SCOPES,
        redirect_uri=REDIRECT_URI
    )

    try:
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials

        # Save credentials to session or DB
        # request.session['credentials'] = { ... } ← optional

        return RedirectResponse(url="/dashboard")  # or wherever you want to go next

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Callback error: {str(e)}")
        
@router.get("/google/authorize-url")
async def get_google_auth_url():
    """Get Google OAuth authorization URL for mobile app"""
    try:
        state = str(uuid.uuid4())
        
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=GOOGLE_SCOPES,
            redirect_uri=REDIRECT_URI
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )
        
        return ApiResponse(
            success=True,
            message="Authorization URL generated successfully",
            data={
                "auth_url": auth_url,
                "state": state,
                "redirect_uri": REDIRECT_URI
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")

@router.post("/google/exchange-token")
async def exchange_google_token(auth_request: AuthTokenRequest):
    """Exchange authorization code for access token"""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=GOOGLE_SCOPES,
            redirect_uri=REDIRECT_URI,
            state=auth_request.state
        )

        # Construct the authorization response URL
        auth_response = f"{REDIRECT_URI}?code={auth_request.code}&state={auth_request.state}"
        flow.fetch_token(authorization_response=auth_response)
        
        credentials = flow.credentials
        
        from services.google_fit import google_fit_service
        credentials_dict = google_fit_service.credentials_to_dict(credentials)
        
        # Create user session
        user_id = session_manager.create_session(google_credentials=credentials_dict)
        
        return AuthTokenResponse(
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expires_in=3600,  # 1 hour default
            user_id=user_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")

@router.post("/refresh-token")
async def refresh_google_token(user_id: str = Header(..., alias="X-User-ID")):
    """Refresh Google access token"""
    try:
        session = session_manager.get_session(user_id)
        if not session or not session.google_credentials:
            raise HTTPException(status_code=401, detail="No valid session found")
        
        from services.google_fit import google_fit_service
        creds = google_fit_service.credentials_from_dict(session.google_credentials)
        refreshed_creds = google_fit_service.refresh_credentials_if_needed(creds)
        
        # Update session with new credentials
        updated_creds_dict = google_fit_service.credentials_to_dict(refreshed_creds)
        session_manager.update_session(user_id, google_credentials=updated_creds_dict)
        
        return ApiResponse(
            success=True,
            message="Token refreshed successfully",
            data={
                "access_token": refreshed_creds.token,
                "expires_in": 3600
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token refresh failed: {str(e)}")

@router.get("/session")
async def get_session_info(user_id: str = Header(..., alias="X-User-ID")):
    """Get current session information"""
    session = session_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ApiResponse(
        success=True,
        message="Session retrieved successfully",
        data={
            "user_id": session.user_id,
            "has_google_auth": session.google_credentials is not None,
            "has_spotify_auth": session.spotify_token is not None,
            "created_at": session.created_at
        }
    )

@router.delete("/logout")
async def logout(user_id: str = Header(..., alias="X-User-ID")):
    """Logout user and clear session"""
    success = session_manager.delete_session(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ApiResponse(
        success=True,
        message="Logged out successfully"
    )
