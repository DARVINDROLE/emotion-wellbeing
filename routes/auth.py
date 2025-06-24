import os
import uuid
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from google_auth_oauthlib.flow import Flow

router = APIRouter()
templates = Jinja2Templates(directory="templates")

CLIENT_SECRETS_FILE = "client_secret.json"
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/authorize")
async def authorize(request: Request):
    # Clear any existing state
    request.session.pop('oauth_state', None)
    
    state = str(uuid.uuid4())
    request.session['oauth_state'] = state
    
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
    
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def callback(request: Request):
    # Check for error parameter
    if request.query_params.get('error'):
        error = request.query_params.get('error')
        error_description = request.query_params.get('error_description', 'No description provided')
        raise HTTPException(status_code=400, detail=f"Authorization error: {error} - {error_description}")
    
    # Check for missing code
    if not request.query_params.get('code'):
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    # State validation
    received_state = request.query_params.get('state')
    stored_state = request.session.get('oauth_state')
    
    if not received_state or not stored_state or received_state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Create flow and fetch token
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=GOOGLE_SCOPES,
        redirect_uri=REDIRECT_URI,
        state=stored_state
    )

    try:
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials
        
        from services.google_fit import google_fit_service
        request.session['credentials'] = google_fit_service.credentials_to_dict(credentials)
        
        # Clear the state after successful authentication
        request.session.pop('oauth_state', None)
        
        return RedirectResponse(url="/dashboard")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during authentication: {str(e)}")

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")
