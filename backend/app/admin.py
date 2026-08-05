from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from app.dependencies.commons import check_admin
from app.dependencies.services import *
from app.models import User
from app.schemas import (
    DoctorCreate,
    DoctorOut,
    SpecialtyCreate,
    SpecialtyOut,
    SpecialtyUpdate,
    AppointmentsSummaryResponse,
    PatientsBySpecialtyResponse,
    RevenueResponse,
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

reports_router = APIRouter(prefix="/reports", tags=["Reports"])

@reports_router.get(
    "/revenue",
    response_model=RevenueResponse,
)
async def get_revenue_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    doctor_id: int | None = Query(None),
    report_service: ReportServiceDep = None,
    current_admin: User = Depends(check_admin),
):
    return await report_service.get_revenue_report(
        start_date, end_date, doctor_id, current_admin
    )

@reports_router.get(
    "/patients-by-specialty",
    response_model=PatientsBySpecialtyResponse
)
async def get_patients_by_specialty(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    report_service: ReportServiceDep = None,
    current_admin: User = Depends(check_admin),
):
    return await report_service.get_patients_by_specialty(
        start_date, end_date, current_admin
    )

@reports_router.get(
    "/appointments-summary",
    response_model=AppointmentsSummaryResponse,
)
async def get_appointments_summary(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    report_service: ReportServiceDep = None,
    current_admin: User = Depends(check_admin),
):
    return await report_service.get_appointments_summary(
        start_date, end_date, current_admin
    )