# models/mental_health.py
from pydantic import BaseModel
from typing import Optional
import uuid

class Condition(BaseModel):
    id: str
    name: str
    description: Optional[str]

class ConditionCreate(BaseModel):
    name: str
    description: Optional[str]

class Medication(BaseModel):
    id: str
    name: str
    dosage: str
    active: bool = True

class MedicationCreate(BaseModel):
    name: str
    dosage: str
