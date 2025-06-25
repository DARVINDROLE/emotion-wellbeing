import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from models.mental_health import Condition, ConditionCreate, Medication, MedicationCreate

class MentalHealthDB:
    def __init__(self, file_path: str = "mental_health_data.json"):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({}, f)
    
    def _load_data(self) -> Dict:
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return {}
    
    def _save_data(self, data: Dict) -> bool:
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def get_user_data(self, user_id: str) -> Dict:
        all_data = self._load_data()
        return all_data.get(user_id, {'conditions': [], 'medications': []})
    
    def save_user_data(self, user_id: str, user_data: Dict) -> bool:
        all_data = self._load_data()
        all_data[user_id] = user_data
        return self._save_data(all_data)
    
    # Condition methods
    def get_conditions(self, user_id: str) -> List[Condition]:
        user_data = self.get_user_data(user_id)
        return [Condition(**condition) for condition in user_data['conditions']]
    
    def add_condition(self, user_id: str, condition_data: ConditionCreate) -> Condition:
        user_data = self.get_user_data(user_id)
        new_condition = Condition(
            id=str(uuid.uuid4()),
            created_at=datetime.now().isoformat(),
            **condition_data.dict()
        )
        user_data['conditions'].append(new_condition.dict())
        self.save_user_data(user_id, user_data)
        return new_condition
    
    def delete_condition(self, user_id: str, condition_id: str) -> bool:
        user_data = self.get_user_data(user_id)
        user_data['conditions'] = [
            c for c in user_data['conditions'] if c['id'] != condition_id
        ]
        return self.save_user_data(user_id, user_data)
    
    # Medication methods
    def get_medications(self, user_id: str) -> List[Medication]:
        user_data = self.get_user_data(user_id)
        return [Medication(**medication) for medication in user_data['medications']]
    
    def add_medication(self, user_id: str, medication_data: MedicationCreate) -> Medication:
        user_data = self.get_user_data(user_id)
        new_medication = Medication(
            id=str(uuid.uuid4()),
            created_at=datetime.now().isoformat(),
            **medication_data.dict()
        )
        user_data['medications'].append(new_medication.dict())
        self.save_user_data(user_id, user_data)
        return new_medication
    
    def delete_medication(self, user_id: str, medication_id: str) -> bool:
        user_data = self.get_user_data(user_id)
        user_data['medications'] = [
            m for m in user_data['medications'] if m['id'] != medication_id
        ]
        return self.save_user_data(user_id, user_data)
    
    def toggle_medication(self, user_id: str, medication_id: str) -> bool:
        user_data = self.get_user_data(user_id)
        for medication in user_data['medications']:
            if medication['id'] == medication_id:
                medication['active'] = not medication.get('active', True)
                break
        return self.save_user_data(user_id, user_data)

# Global database instance
mental_health_db = MentalHealthDB()