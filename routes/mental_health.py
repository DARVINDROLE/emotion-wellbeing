from fastapi import APIRouter, HTTPException, Header
from typing import List
from models.mental_health import Condition, ConditionCreate, Medication, MedicationCreate
from models.api_response import ApiResponse
from database.mental_health_db import mental_health_db

router = APIRouter()

@router.get("/conditions")
async def get_conditions(user_id: str = Header(..., alias="X-User-ID")):
    """Get user's mental health conditions"""
    try:
        conditions = mental_health_db.get_conditions(user_id)
        return ApiResponse(
            success=True,
            message="Conditions retrieved successfully",
            data=[condition.dict() for condition in conditions]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conditions: {str(e)}")

@router.post("/conditions")
async def add_condition(
    condition: ConditionCreate,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Add new mental health condition"""
    try:
        new_condition = mental_health_db.add_condition(user_id, condition)
        return ApiResponse(
            success=True,
            message="Condition added successfully",
            data=new_condition.dict()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add condition: {str(e)}")

@router.delete("/conditions/{condition_id}")
async def delete_condition(
    condition_id: str,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Delete mental health condition"""
    try:
        success = mental_health_db.delete_condition(user_id, condition_id)
        if not success:
            raise HTTPException(status_code=404, detail="Condition not found")
        
        return ApiResponse(
            success=True,
            message="Condition deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete condition: {str(e)}")

@router.get("/medications")
async def get_medications(user_id: str = Header(..., alias="X-User-ID")):
    """Get user's medications"""
    try:
        medications = mental_health_db.get_medications(user_id)
        return ApiResponse(
            success=True,
            message="Medications retrieved successfully",
            data=[medication.dict() for medication in medications]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get medications: {str(e)}")

@router.post("/medications")
async def add_medication(
    medication: MedicationCreate,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Add new medication"""
    try:
        new_medication = mental_health_db.add_medication(user_id, medication)
        return ApiResponse(
            success=True,
            message="Medication added successfully",
            data=new_medication.dict()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add medication: {str(e)}")

@router.delete("/medications/{medication_id}")
async def delete_medication(
    medication_id: str,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Delete medication"""
    try:
        success = mental_health_db.delete_medication(user_id, medication_id)
        if not success:
            raise HTTPException(status_code=404, detail="Medication not found")
        
        return ApiResponse(
            success=True,
            message="Medication deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete medication: {str(e)}")

@router.put("/medications/{medication_id}/toggle")
async def toggle_medication(
    medication_id: str,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Toggle medication active status"""
    try:
        success = mental_health_db.toggle_medication(user_id, medication_id)
        if not success:
            raise HTTPException(status_code=404, detail="Medication not found")
        
        return ApiResponse(
            success=True,
            message="Medication status updated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update medication: {str(e)}")


