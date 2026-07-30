from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SpecialtyCreate, SpecialtyOut, SpecialtyUpdate
from app.services import SpecialtyService
from app.models import User
from app.dependencies import get_current_admin

router = APIRouter(prefix="/admin",tags=["Admin"])

specialty_service = SpecialtyService()

@router.post("/specialties",response_model=SpecialtyOut,status_code=201)
def create_specialty(specialty: SpecialtyCreate,db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    try:
        return specialty_service.create_specialty(db, specialty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/specialties/{specialty_id}/status",response_model=SpecialtyOut)
def toggle_specialty_status(specialty_id: int,db: Session = Depends(get_db),current_admin: User = Depends(get_current_admin)):
    try:
        return specialty_service.toggle_specialty_status(db,specialty_id)
    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e))

@router.put("/specialties/{specialty_id}",response_model=SpecialtyOut)
def update_specialty(specialty_id: int,specialty_data: SpecialtyUpdate,db: Session = Depends(get_db),current_admin: User = Depends(get_current_admin)):
    try:
        return specialty_service.update_specialty(db,specialty_id,specialty_data)

    except ValueError as e:
        if str(e) == "Specialty not found":
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))
