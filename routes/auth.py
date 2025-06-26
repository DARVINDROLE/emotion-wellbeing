import os
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow

router = APIRouter()

# LIVE REDIRECT URL (Google must be configured to allow this)
REDIRECT_URI = "https://emotion-wellbeing.onrender.com/callback"
DEEP_LINK_URI = "myapp://auth-success"  # Custom scheme for Android deep linking

CLIENT_SECRETS_FILE = "client_secret.json"
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for local/HTTP dev

# Temporary stores (in-memory)
STATE_CACHE = {}
CREDENTIAL_CACHE = {}


@router.get("/authorize")
async def authorize():
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
    STATE_CACHE[state] = True
    return JSONResponse(content={"auth_url": auth_url})


@router.get("/callback")
async def callback(request: Request):
    error = request.query_params.get('error')
    if error:
        return JSONResponse(status_code=400, content={"error": error})

    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if not code or not state or state not in STATE_CACHE:
        return JSONResponse(status_code=400, content={"error": "Invalid state or code"})

    del STATE_CACHE[state]

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=GOOGLE_SCOPES,
        redirect_uri=REDIRECT_URI,
        state=state
    )

    try:
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials

        from services.google_fit import google_fit_service
        CREDENTIAL_CACHE[state] = google_fit_service.credentials_to_dict(credentials)

        # 🔁 Return to Android app via deep link with `state`
        return RedirectResponse(url=f"{DEEP_LINK_URI}?state={state}")

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@router.get("/credentials")
async def get_credentials(state: str):
    if state not in CREDENTIAL_CACHE:
        return JSONResponse(status_code=404, content={"error": "No credentials found"})
    return JSONResponse(content=CREDENTIAL_CACHE[state])


@router.get("/logout")
async def logout(state: str):
    CREDENTIAL_CACHE.pop(state, None)
    return JSONResponse(content={"message": "Logged out"})

