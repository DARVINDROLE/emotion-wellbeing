import os
import httpx
from fastapi import HTTPException
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from models.fitness import StepData, HeartRateData, SleepData

class GoogleFitService:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/fitness.activity.read',
            'https://www.googleapis.com/auth/fitness.heart_rate.read',
            'https://www.googleapis.com/auth/fitness.sleep.read'
        ]
    
    def credentials_from_dict(self, creds_dict: dict) -> Credentials:
        expiry = None
        if creds_dict.get('expiry'):
            try:
                expiry = datetime.fromisoformat(creds_dict['expiry'].replace('Z', '+00:00'))
            except Exception as e:
                print(f"Error parsing expiry date: {e}")
        
        return Credentials(
            token=creds_dict['token'],
            refresh_token=creds_dict['refresh_token'],
            token_uri=creds_dict['token_uri'],
            client_id=creds_dict['client_id'],
            client_secret=creds_dict['client_secret'],
            scopes=creds_dict['scopes'],
            expiry=expiry
        )
    
    def credentials_to_dict(self, credentials: Credentials) -> dict:
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    def refresh_credentials_if_needed(self, creds: Credentials) -> Credentials:
        if creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired credentials...")
                creds.refresh(GoogleRequest())
                return creds
            except Exception as e:
                print(f"Failed to refresh credentials: {e}")
                raise HTTPException(status_code=401, detail="Failed to refresh credentials")
        return creds
    
    async def get_fitness_data(self, credentials_dict: dict) -> Tuple[List[StepData], List[HeartRateData], List[SleepData]]:
        creds = self.credentials_from_dict(credentials_dict)
        creds = self.refresh_credentials_if_needed(creds)
        
        # Prepare time range (last 7 days)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        start_time_millis = int(start_time.timestamp() * 1000)
        end_time_millis = int(end_time.timestamp() * 1000)

        headers = {
            'Authorization': f'Bearer {creds.token}',
            'Content-Type': 'application/json'
        }

        data = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"},
                {"dataTypeName": "com.google.heart_rate.bpm"},
                {"dataTypeName": "com.google.sleep.segment"}
            ],
            "bucketByTime": {"durationMillis": 86400000},  # 24 hours
            "startTimeMillis": start_time_millis,
            "endTimeMillis": end_time_millis
        }

        step_data, heart_rate_data, sleep_data = [], [], []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate',
                    headers=headers,
                    json=data,
                    timeout=30
                )

            if response.status_code == 200:
                fit_data = response.json()

                for bucket in fit_data.get('bucket', []):
                    bucket_start = datetime.fromtimestamp(int(bucket['startTimeMillis']) / 1000)
                    date_str = bucket_start.strftime('%Y-%m-%d')
                    
                    for dataset in bucket.get('dataset', []):
                        source = dataset.get('dataSourceId', '')
                        
                        for point in dataset.get('point', []):
                            if 'step_count' in source:
                                steps = point['value'][0].get('intVal', 0)
                                step_data.append(StepData(date=date_str, steps=steps))
                            elif 'heart_rate' in source:
                                bpm = point['value'][0].get('fpVal', 0.0)
                                heart_rate_data.append(HeartRateData(date=date_str, bpm=round(bpm, 1)))
                            elif 'sleep' in source:
                                stage = point['value'][0].get('intVal', -1)
                                sleep_data.append(SleepData(date=date_str, stage=stage))

                # Sort data by date
                step_data.sort(key=lambda x: x.date)
                heart_rate_data.sort(key=lambda x: x.date)
                sleep_data.sort(key=lambda x: x.date)

        except Exception as e:
            print(f"Google Fit API error: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch fitness data")

        return step_data, heart_rate_data, sleep_data, self.credentials_to_dict(creds)

google_fit_service = GoogleFitService()
