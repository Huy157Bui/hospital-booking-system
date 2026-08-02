from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User
from app.schemas import (
    DoctorCreate,
    DoctorOut,
    SpecialtyCreate,
    SpecialtyOut,
    SpecialtyUpdate,
)
from app.services import DoctorService, SpecialtyService

router = APIRouter(prefix="/admin", tags=["Admin"])

specialty_service = SpecialtyService()
doctor_service = DoctorService()


@router.post("/specialties", response_model=SpecialtyOut, status_code=201)
async def create_specialty(
    specialty: SpecialtyCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    try:
        return await specialty_service.create_specialty(db, specialty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/specialties/{specialty_id}/status", response_model=SpecialtyOut)
async def toggle_specialty_status(
    specialty_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    try:
        return await specialty_service.toggle_specialty_status(db, specialty_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/specialties/{specialty_id}", response_model=SpecialtyOut)
async def update_specialty(
    specialty_id: int,
    specialty_data: SpecialtyUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    try:
        return await specialty_service.update_specialty(
            db, specialty_id, specialty_data
        )
    except ValueError as e:
        if str(e) == "Specialty not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/doctors", response_model=DoctorOut, status_code=201)
async def create_doctor(
    doctor_data: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    try:
        return await doctor_service.create_doctor(db, doctor_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
