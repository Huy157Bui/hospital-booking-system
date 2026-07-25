from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SpecialtyCreate, SpecialtyOut
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

