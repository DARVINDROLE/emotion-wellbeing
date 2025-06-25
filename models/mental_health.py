from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class SeverityLevel(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

class ConditionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    diagnosed_date: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.MILD
    notes: Optional[str] = None

class ConditionCreate(ConditionBase):
    pass

class Condition(ConditionBase):
    id: str
    created_at: str

    class Config:
        from_attributes = True

class MedicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    started_date: Optional[str] = None
    prescribing_doctor: Optional[str] = None
    notes: Optional[str] = None
    active: bool = True

class MedicationCreate(MedicationBase):
    pass

class Medication(MedicationBase):
    id: str
    created_at: str

    class Config:
        from_attributes = True

