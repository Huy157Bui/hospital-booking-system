from datetime import datetime
from fastapi import APIRouter, Depends, Query

from app.dependencies.commons import check_admin
from app.dependencies.services import (
    DoctorServiceDep,
    ReportServiceDep,
    SpecialtyServiceDep,
    UserServiceDep,
    PatientServiceDep,
    AppointmentServiceDep,
    MedicineServiceDep,
)
from app.models import User, UserRole, AppointmentStatus
from app.schemas import (
    DoctorCreate,
    DoctorOut,
    DoctorUpdate,
    SpecialtyCreate,
    SpecialtyOut,
    SpecialtyUpdate,
    AppointmentsSummaryResponse,
    PatientsBySpecialtyResponse,
    RevenueResponse,
    UserOut,
    UserUpdate,
    PatientOut,
    PatientUpdate,
    AppointmentOut,
    AppointmentCancel,
    MedicineOut,
    MedicineCreate,
    MedicineUpdate,
    DashboardSummaryResponse,
)

admin_router = APIRouter(prefix="/admin", tags=["Admin"])
reports_router = APIRouter(prefix="/reports", tags=["Reports"])


@reports_router.get("/dashboard-summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    report_service: ReportServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await report_service.get_dashboard_summary()


@reports_router.get("/revenue", response_model=RevenueResponse)
async def get_revenue_report(
    report_service: ReportServiceDep,
    start_date: datetime = Query(..., description="YYYY-MM-DDTHH:MM:SS"),
    end_date: datetime = Query(..., description="YYYY-MM-DDTHH:MM:SS"),
    doctor_id: int | None = None,
    current_admin: User = Depends(check_admin),
):
    return await report_service.get_revenue_report(start_date, end_date, doctor_id, current_admin)


@reports_router.get("/patients-by-specialty", response_model=PatientsBySpecialtyResponse)
async def get_patients_by_specialty(
    report_service: ReportServiceDep,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_admin: User = Depends(check_admin),
):
    return await report_service.get_patients_by_specialty(start_date, end_date, current_admin)


@reports_router.get("/appointments-summary", response_model=AppointmentsSummaryResponse)
async def get_appointments_summary(
    report_service: ReportServiceDep,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_admin: User = Depends(check_admin),
):
    return await report_service.get_appointments_summary(start_date, end_date, current_admin)


@admin_router.get("/users", response_model=list[UserOut])
async def get_all_users(
    user_service: UserServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    role: UserRole | None = None,
    is_active: bool | None = None,
    current_admin: User = Depends(check_admin),
):
    return await user_service.get_all_users(skip=skip, limit=limit, role=role, is_active=is_active)


@admin_router.put("/users/{user_id}", response_model=UserOut)
async def update_user_by_admin(
    user_id: int,
    update_data: UserUpdate,
    user_service: UserServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await user_service.update_user_by_admin(user_id, update_data)


@admin_router.patch("/users/{user_id}/status", response_model=UserOut)
async def toggle_user_status(
    user_id: int,
    user_service: UserServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await user_service.toggle_user_status(user_id)


@admin_router.get("/doctors", response_model=list[DoctorOut])
async def admin_get_all_doctors(
    doctor_service: DoctorServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: str | None = Query(None, description="active, inactive, v.v."),
    current_admin: User = Depends(check_admin),
):
    return await doctor_service.get_all_doctors_admin(skip=skip, limit=limit, status=status)


@admin_router.post("/doctors", response_model=DoctorOut, status_code=201)
async def admin_create_doctor(
    doctor_data: DoctorCreate,
    doctor_service: DoctorServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await doctor_service.create_doctor(doctor_data)


@admin_router.put("/doctors/{doctor_id}", response_model=DoctorOut)
async def admin_update_doctor(
    doctor_id: int,
    update_data: DoctorUpdate,
    doctor_service: DoctorServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await doctor_service.update_doctor_by_admin(doctor_id, update_data)


@admin_router.patch("/doctors/{doctor_id}/status", response_model=DoctorOut)
async def admin_toggle_doctor_status(
    doctor_id: int,
    doctor_service: DoctorServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await doctor_service.toggle_doctor_status(doctor_id)


@admin_router.get("/patients", response_model=list[PatientOut])
async def get_all_patients(
    patient_service: PatientServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    current_admin: User = Depends(check_admin),
):
    return await patient_service.get_all_patients(skip=skip, limit=limit)


@admin_router.put("/patients/{patient_id}", response_model=PatientOut)
async def update_patient_by_admin(
    patient_id: int,
    update_data: PatientUpdate,
    patient_service: PatientServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await patient_service.update_patient_by_admin(patient_id, update_data)


@admin_router.get("/appointments", response_model=list[AppointmentOut])
async def admin_get_all_appointments(
    appointment_service: AppointmentServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: AppointmentStatus | None = None,
    doctor_id: int | None = None,
    current_admin: User = Depends(check_admin),
):
    return await appointment_service.get_all_appointments_admin(
        skip=skip, limit=limit, status=status, doctor_id=doctor_id
    )


@admin_router.patch("/appointments/{appointment_id}/force-cancel", response_model=AppointmentOut)
async def admin_force_cancel_appointment(
    appointment_id: int,
    cancel_data: AppointmentCancel,
    appointment_service: AppointmentServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await appointment_service.force_cancel_appointment(
        appointment_id, cancel_data.cancel_reason
    )


@admin_router.get("/medicines", response_model=list[MedicineOut])
async def get_all_medicines(
    medicine_service: MedicineServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    current_admin: User = Depends(check_admin),
):
    return await medicine_service.get_all_medicines_admin(skip=skip, limit=limit)


@admin_router.post("/medicines", response_model=MedicineOut, status_code=201)
async def create_medicine(
    data: MedicineCreate,
    medicine_service: MedicineServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await medicine_service.create_medicine(data)


@admin_router.put("/medicines/{medicine_id}", response_model=MedicineOut)
async def update_medicine(
    medicine_id: int,
    data: MedicineUpdate,
    medicine_service: MedicineServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await medicine_service.update_medicine(medicine_id, data)


@admin_router.patch("/medicines/{medicine_id}/status", response_model=MedicineOut)
async def toggle_medicine_status(
    medicine_id: int,
    medicine_service: MedicineServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await medicine_service.toggle_medicine_status(medicine_id)


@admin_router.post("/specialties", response_model=SpecialtyOut, status_code=201)
async def create_specialty(
    specialty: SpecialtyCreate,
    specialty_service: SpecialtyServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await specialty_service.create_specialty(specialty)


@admin_router.patch("/specialties/{specialty_id}/status", response_model=SpecialtyOut)
async def toggle_specialty_status(
    specialty_id: int,
    specialty_service: SpecialtyServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await specialty_service.toggle_specialty_status(specialty_id)


@admin_router.put("/specialties/{specialty_id}", response_model=SpecialtyOut)
async def update_specialty(
    specialty_id: int,
    specialty_data: SpecialtyUpdate,
    specialty_service: SpecialtyServiceDep,
    current_admin: User = Depends(check_admin),
):
    return await specialty_service.update_specialty(specialty_id, specialty_data)


#@admin_router.patch("/doctors/{doctor_id}/specialty", response_model=DoctorOut)
#async def admin_assign_doctor_specialty(
#    doctor_id: int,
#    specialty_id: int | None,
#    doctor_service: DoctorServiceDep,
#    current_admin: User = Depends(check_admin),
#):
#    return await doctor_service.assign_specialty(doctor_id, specialty_id)