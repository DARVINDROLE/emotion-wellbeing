import os
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from starlette.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter()

# 🌐 YOUR DEPLOYED RENDER BACKEND URL
BASE_URL = "https://your-backend.onrender.com"
CLIENT_SECRETS_FILE = "client_secret.json"
REDIRECT_URI = f"{BASE_URL}/callback"

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Remove in production

# CORS & Session Setup
app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="your-super-secret-key")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-website.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# In-memory storage (temporary for demo; use Redis or DB in prod)
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

    STATE_CACHE[state] = True  # store state

    return JSONResponse(content={"auth_url": auth_url})


@router.get("/callback")
async def callback(request: Request):
    error = request.query_params.get('error')
    if error:
        return JSONResponse(status_code=400, content={"error": error})

    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if not code or not state or state not in STATE_CACHE:
        return JSONResponse(status_code=400, content={"error": "Invalid request or missing state"})

    del STATE_CACHE[state]  # remove used state

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
        cred_dict = google_fit_service.credentials_to_dict(credentials)

        # Store credentials temporarily (you can return access token or save to DB)
        CREDENTIAL_CACHE[state] = cred_dict

        # Redirect to frontend with a token (or session ID)
        return RedirectResponse(url=f"https://your-frontend-website.com/dashboard?state={state}")

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@router.get("/credentials")
async def get_credentials(state: str):
    creds = CREDENTIAL_CACHE.get(state)
    if not creds:
        return JSONResponse(status_code=404, content={"error": "Credentials not found"})
    return JSONResponse(content=creds)


@router.get("/logout")
async def logout(state: str):
    CREDENTIAL_CACHE.pop(state, None)
    return JSONResponse(content={"message": "Logged out"})

