# test_firebase_connection.py
from services.firebase import db

def test_connection():
    doc_ref = db.collection("test").document("status")
    doc_ref.set({"ping": "ok"})
    print("✅ Successfully wrote to Firebase!")

if __name__ == "__main__":
    test_connection()
