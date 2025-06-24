from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routes import auth
from routes import dashboard, mental_health, spotify

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI(
    title="Health & Music Mobile API",
    description="RESTful API for mobile app - Google Fit data, Spotify listening activity, and mental health tracking",
    version="3.0.0"
)

# Add CORS middleware for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(mental_health.router, prefix="/api/mental-health", tags=["Mental Health"])
app.include_router(spotify.router, prefix="/api/spotify", tags=["Spotify"])

@app.get("/")
async def root():
    return {
        "message": "Health & Music Mobile API", 
        "version": "3.0.0",
        "docs": "/docs",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)