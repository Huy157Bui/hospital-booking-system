from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.commons import check_admin
from app.dependencies.db import get_db
from app.dependencies.services import *
from app.models import User
from app.schemas import (
    DoctorCreate,
    DoctorOut,
    SpecialtyCreate,
    SpecialtyOut,
    SpecialtyUpdate,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/specialties", response_model=SpecialtyOut, status_code=201)
async def create_specialty(
    specialty: SpecialtyCreate,
    specialty_service: SpecialtyServiceDep,
    current_admin: User = Depends(check_admin),
):
    try:
        return await specialty_service.create_specialty(specialty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/specialties/{specialty_id}/status", response_model=SpecialtyOut)
async def toggle_specialty_status(
    specialty_id: int,
    specialty_service: SpecialtyServiceDep,
    current_admin: User = Depends(check_admin),
):
    try:
        return await specialty_service.toggle_specialty_status(specialty_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/specialties/{specialty_id}", response_model=SpecialtyOut)
async def update_specialty(
    specialty_id: int,
    specialty_data: SpecialtyUpdate,
    specialty_service: SpecialtyServiceDep,
    current_admin: User = Depends(check_admin),
):
    try:
        return await specialty_service.update_specialty(specialty_id, specialty_data)
    except ValueError as e:
        if str(e) == "Specialty not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/doctors", response_model=DoctorOut, status_code=201)
async def create_doctor(
    doctor_data: DoctorCreate,
    doctor_service: DoctorServiceDep,
    current_admin: User = Depends(check_admin),
):
    try:
        return await doctor_service.create_doctor(doctor_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
