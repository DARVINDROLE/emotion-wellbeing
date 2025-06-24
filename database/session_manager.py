# session_manager.py (Firebase Integrated)
import uuid
from datetime import datetime
from typing import Optional
from routes.auth import UserSession
from services.firebase import db

class SessionManager:
    def create_session(self, google_credentials: dict = None, spotify_token: dict = None) -> str:
        user_id = str(uuid.uuid4())
        session = UserSession(
            user_id=user_id,
            google_credentials=google_credentials,
            spotify_token=spotify_token,
            created_at=datetime.now().isoformat()
        )
        db.collection("sessions").document(user_id).set(session.dict())
        return user_id

    def get_session(self, user_id: str) -> Optional[UserSession]:
        doc = db.collection("sessions").document(user_id).get()
        if doc.exists:
            return UserSession(**doc.to_dict())
        return None

    def update_session(self, user_id: str, google_credentials: dict = None, spotify_token: dict = None) -> bool:
        update_data = {}
        if google_credentials:
            update_data["google_credentials"] = google_credentials
        if spotify_token:
            update_data["spotify_token"] = spotify_token
        if update_data:
            db.collection("sessions").document(user_id).update(update_data)
            return True
        return False

    def delete_session(self, user_id: str) -> bool:
        db.collection("sessions").document(user_id).delete()
        return True

# Global session manager instance
session_manager = SessionManager()
