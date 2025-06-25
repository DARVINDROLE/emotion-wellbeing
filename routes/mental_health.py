from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List
from models.mental_health import Condition, ConditionCreate, Medication, MedicationCreate
from database.mental_health_db import mental_health_db

router = APIRouter()

def get_current_user_id(request: Request) -> str:
    """Get current user ID from session"""
    if 'credentials' not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.session['credentials'].get('client_id', 'default_user')

@router.get("/conditions", response_model=List[Condition])
async def get_conditions(request: Request):
    user_id = get_current_user_id(request)
    return mental_health_db.get_conditions(user_id)

@router.post("/conditions", response_model=Condition)
async def add_condition(condition: ConditionCreate, request: Request):
    user_id = get_current_user_id(request)
    return mental_health_db.add_condition(user_id, condition)

@router.delete("/conditions/{condition_id}")
async def delete_condition(condition_id: str, request: Request):
    user_id = get_current_user_id(request)
    success = mental_health_db.delete_condition(user_id, condition_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete condition")
    return {"success": True}

@router.get("/medications", response_model=List[Medication])
async def get_medications(request: Request):
    user_id = get_current_user_id(request)
    return mental_health_db.get_medications(user_id)

@router.post("/medications", response_model=Medication)
async def add_medication(medication: MedicationCreate, request: Request):
    user_id = get_current_user_id(request)
    return mental_health_db.add_medication(user_id, medication)

@router.delete("/medications/{medication_id}")
async def delete_medication(medication_id: str, request: Request):
    user_id = get_current_user_id(request)
    success = mental_health_db.delete_medication(user_id, medication_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete medication")
    return {"success": True}

@router.put("/medications/{medication_id}/toggle")
async def toggle_medication(medication_id: str, request: Request):
    user_id = get_current_user_id(request)
    success = mental_health_db.toggle_medication(user_id, medication_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update medication")
    return {"success": True}
