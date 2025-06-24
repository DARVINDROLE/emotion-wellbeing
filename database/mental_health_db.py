from typing import List
from models.mental_health import Condition, ConditionCreate, Medication, MedicationCreate
from services.firebase import db
import uuid

class MentalHealthDB:
    def get_conditions(self, user_id: str) -> List[Condition]:
        docs = db.collection("users").document(user_id).collection("conditions").stream()
        return [Condition(id=doc.id, **doc.to_dict()) for doc in docs]

    def add_condition(self, user_id: str, data: ConditionCreate) -> Condition:
        new_id = str(uuid.uuid4())
        db.collection("users").document(user_id).collection("conditions").document(new_id).set({
            "name": data.name,
            "description": data.description
        })
        return Condition(id=new_id, name=data.name, description=data.description)

    def delete_condition(self, user_id: str, condition_id: str) -> bool:
        db.collection("users").document(user_id).collection("conditions").document(condition_id).delete()
        return True

    def get_medications(self, user_id: str) -> List[Medication]:
        docs = db.collection("users").document(user_id).collection("medications").stream()
        return [Medication(id=doc.id, **doc.to_dict()) for doc in docs]

    def add_medication(self, user_id: str, data: MedicationCreate) -> Medication:
        new_id = str(uuid.uuid4())
        db.collection("users").document(user_id).collection("medications").document(new_id).set({
            "name": data.name,
            "dosage": data.dosage,
            "active": True
        })
        return Medication(id=new_id, name=data.name, dosage=data.dosage, active=True)

    def delete_medication(self, user_id: str, med_id: str) -> bool:
        db.collection("users").document(user_id).collection("medications").document(med_id).delete()
        return True

    def toggle_medication(self, user_id: str, med_id: str) -> bool:
        doc_ref = db.collection("users").document(user_id).collection("medications").document(med_id)
        doc = doc_ref.get()
        if doc.exists:
            current = doc.to_dict().get("active", True)
            doc_ref.update({"active": not current})
            return True
        return False

# Export global instance
mental_health_db = MentalHealthDB()
