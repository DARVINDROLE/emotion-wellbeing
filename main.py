from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware  # Changed this line
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv

from routes import auth, dashboard, mental_health, spotify
import os
from dotenv import load_dotenv

from routes import auth, dashboard, mental_health, spotify

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI(
    title="Health & Music Dashboard",
    description="Your Google Fit data, Spotify listening activity, and mental health tracking in one place",
    version="2.0.0"
)

# Add session middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("FLASK_SECRET_KEY", "super-secret-key-123")
)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(mental_health.router, prefix="/api/mental-health", tags=["Mental Health"])
app.include_router(spotify.router, prefix="/spotify", tags=["Spotify"])

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return {"message": "Health & Music Dashboard API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
