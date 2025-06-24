# models/fitness.py
from pydantic import BaseModel
from typing import Optional, List


class StepData(BaseModel):
    timestamp: str
    steps: int


class HeartRateData(BaseModel):
    timestamp: str
    bpm: int


class SleepData(BaseModel):
    timestamp: str
    duration_minutes: int
    type: str


class SpotifyTrack(BaseModel):
    name: str
    artist: str
    album: Optional[str] = None
    image: Optional[str] = None
    played_at: Optional[str] = None


class DashboardData(BaseModel):
    step_data: List[StepData]
    heart_rate_data: List[HeartRateData]
    sleep_data: List[SleepData]
    current_track: Optional[SpotifyTrack]
    recent_tracks: List[SpotifyTrack]
    spotify_connected: bool
