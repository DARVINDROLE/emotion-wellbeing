from services.firebase import db
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time
from datetime import datetime, timedelta

class GoogleFitService:
    def credentials_to_dict(self, credentials):
        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }

    def credentials_from_dict(self, creds_dict):
        return Credentials(**creds_dict)

    def refresh_credentials_if_needed(self, credentials):
        from google.auth.transport.requests import Request
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        return credentials

    def nanoseconds_since_epoch(self, dt):
        return int(dt.timestamp() * 1e9)

    async def get_fitness_data(self, credentials_dict, user_id: str):
        creds = self.credentials_from_dict(credentials_dict)
        creds = self.refresh_credentials_if_needed(creds)

        service = build("fitness", "v1", credentials=creds)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=1)

        def aggregate(data_type_name, bucket_duration_millis):
            return service.users().dataset().aggregate(userId="me", body={
                "aggregateBy": [{"dataTypeName": data_type_name}],
                "bucketByTime": {"durationMillis": bucket_duration_millis},
                "startTimeMillis": int(start_time.timestamp() * 1000),
                "endTimeMillis": int(end_time.timestamp() * 1000)
            }).execute()

        steps_raw = aggregate("com.google.step_count.delta", 3600000)
        steps = []
        for bucket in steps_raw.get("bucket", []):
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    steps.append({
                        "timestamp": datetime.fromtimestamp(int(point["endTimeNanos"]) / 1e9).isoformat(),
                        "steps": point["value"][0]["intVal"]
                    })

        heart_raw = aggregate("com.google.heart_rate.bpm", 3600000)
        heart = []
        for bucket in heart_raw.get("bucket", []):
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    heart.append({
                        "timestamp": datetime.fromtimestamp(int(point["endTimeNanos"]) / 1e9).isoformat(),
                        "bpm": point["value"][0]["fpVal"]
                    })

        sleep_response = service.users().sessions().list(userId="me", startTime=start_time.isoformat() + "Z", endTime=end_time.isoformat() + "Z").execute()
        sleep = []
        for session in sleep_response.get("session", []):
            if session.get("activityType") == 72:
                start = datetime.fromisoformat(session["startTime"][:-1])
                end = datetime.fromisoformat(session["endTime"][:-1])
                duration = int((end - start).total_seconds() / 60)
                sleep.append({
                    "timestamp": session["startTime"],
                    "duration_minutes": duration,
                    "type": session.get("name", "sleep")
                })

        try:
            fitness_ref = db.collection("users").document(user_id).collection("fitness")
            fitness_ref.document("steps").set({"data": steps})
            print(f"[Firebase] Stored {len(steps)} step records for user {user_id}")

            fitness_ref.document("heart_rate").set({"data": heart})
            print(f"[Firebase] Stored {len(heart)} heart rate records for user {user_id}")

            fitness_ref.document("sleep").set({"data": sleep})
            print(f"[Firebase] Stored {len(sleep)} sleep records for user {user_id}")
        except Exception as e:
            print(f"[Firebase Error] Failed to store fitness data for user {user_id}: {e}")

        return steps, heart, sleep, self.credentials_to_dict(creds)

    def get_stored_google_fit_data(self, user_id: str):
        fitness_ref = db.collection("users").document(user_id).collection("fitness")
        steps = fitness_ref.document("steps").get().to_dict()
        heart = fitness_ref.document("heart_rate").get().to_dict()
        sleep = fitness_ref.document("sleep").get().to_dict()
        return (
            steps.get("data", []) if steps else [],
            heart.get("data", []) if heart else [],
            sleep.get("data", []) if sleep else []
        )

google_fit_service = GoogleFitService()
