from fastapi import APIRouter, HTTPException, Depends
from app.dependencies.commons import check_admin
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
        return await specialty_service.create_specialty(specialty)


@router.patch("/specialties/{specialty_id}/status", response_model=SpecialtyOut)
async def toggle_specialty_status(
    specialty_id: int,
    specialty_service: SpecialtyServiceDep,
    current_admin: User = Depends(check_admin),
):
        return await specialty_service.toggle_specialty_status(specialty_id)

@router.put("/specialties/{specialty_id}", response_model=SpecialtyOut)
async def update_specialty(
    specialty_id: int,
    specialty_data: SpecialtyUpdate,
    specialty_service: SpecialtyServiceDep,
    current_admin: User = Depends(check_admin),
):
        return await specialty_service.update_specialty(specialty_id, specialty_data)


@router.post("/doctors", response_model=DoctorOut, status_code=201)
async def create_doctor(
    doctor_data: DoctorCreate,
    doctor_service: DoctorServiceDep,
    current_admin: User = Depends(check_admin),
):
        return await doctor_service.create_doctor(doctor_data)
