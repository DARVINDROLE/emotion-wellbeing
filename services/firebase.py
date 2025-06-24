# services/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase app only once
cred = credentials.Certificate("firebase_service_account.json")  # path to your downloaded key
firebase_admin.initialize_app(cred)

db = firestore.client()
