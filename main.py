from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import routers
from routes.auth import router as auth_router
from routes import dashboard, mental_health, spotify

# Initialize app
app = FastAPI(
    title="Health & Music Dashboard",
    description="Your Google Fit data, Spotify listening activity, and mental health tracking in one place",
    version="2.0.0"
)

# CORS Middleware — ✅ Must come before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # ✅ Your local HTML project
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Middleware — also before routers
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("FLASK_SECRET_KEY", "super-secret-key-123")
)

# Routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(mental_health.router, prefix="/api/mental-health", tags=["Mental Health"])
app.include_router(spotify.router, prefix="/spotify", tags=["Spotify"])

# Templates (optional)
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return {"message": "Health & Music Dashboard API", "docs": "/docs"}

# Only for local run (Render will ignore this)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)

