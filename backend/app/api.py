from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.commons import (
    get_current_user,
    get_current_patient_profile,
    get_appointment_record_access,
    get_current_doctor_profile,
    check_doctor,
    get_owned_schedule_slot,
)
from app.dependencies.db import get_db
from app.dependencies.services import *
from app.models import Patient, ScheduleSlot, User, Doctor, Appointment
from app.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentOut,
    DoctorOut,
    DoctorScheduleOut,
    LoginRequest,
    ScheduleOut,
    ScheduleSlotOut,
    ScheduleSlotUpdate,
    ScheduleUpdate,
    SpecialtyOut,
    Token,
    UserCreate,
    UserOut,
    AppointmentStatusUpdate,
    ExaminationRecordCreate,
    ExaminationOut,
    PatientMedicalHistoryOut,
)

router = APIRouter(prefix="")


@router.post(
    "/register", tags=["Authentication"], response_model=UserOut, status_code=201
)
async def register(user_data: UserCreate, auth_service: AuthServiceDep):
    try:
        return await auth_service.register(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", tags=["Authentication"], response_model=Token)
async def login(login_data: LoginRequest, auth_service: AuthServiceDep):
    try:
        result = await auth_service.login(login_data.username, login_data.password)
        user_out = UserOut.model_validate(result["user"])
        return Token(
            access_token=result["access_token"],
            token_type=result["token_type"],
            user=user_out,
        )
    except ValueError as e:
        if str(e) == "Invalid username or password":
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/me", tags=["Users"], response_model=UserOut)
async def get_my_profile(
    user_service: UserServiceDep,
    current_user: User = Depends(get_current_user),
):
    return user_service.get_profile(current_user)


@router.get(
    "/me/medical-records", response_model=PatientMedicalHistoryOut, tags=["Patients"]
)
async def get_my_medical_records(
    patient_service: PatientServiceDep,
    patient: Patient = Depends(get_current_patient_profile),
):
    result = await patient_service.get_patient_medical_history(patient.id)
    return PatientMedicalHistoryOut(
        medical_record=result["medical_record"],
        examinations=result["examinations"],
    )

appointments_router = APIRouter(prefix="/appointments", tags=["Appointments"])

@appointments_router.get("/users/me/appointments", response_model=list[AppointmentOut])
async def get_my_appointments(
    appointment_service: AppointmentServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.get_user_appointments(current_user)


@appointments_router.post("", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    appointment_data: AppointmentCreate,
    appointment_service: AppointmentServiceDep,
    patient: Patient = Depends(get_current_patient_profile),
):
    return await appointment_service.create_appointment(patient, appointment_data)


@appointments_router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment_detail(
    appointment_id: int,
    appointment_service: AppointmentServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.get_accessible_appointment(
        appointment_id, current_user
    )


@appointments_router.patch("/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appointment_id: int,
    cancel_data: AppointmentCancel,
    appointment_service: AppointmentServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.cancel_appointment(
        appointment_id, current_user, cancel_data
    )


@appointments_router.patch("/{appointment_id}/status", response_model=AppointmentOut)
async def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    appointment_service: AppointmentServiceDep,
    doctor: Doctor = Depends(get_current_doctor_profile),
):
    return await appointment_service.update_appointment_status(
        appointment_id, status_update.status, doctor
    )


@appointments_router.post("/{appointment_id}/record", response_model=ExaminationOut)
async def add_examination_record(
    appointment_id: int,
    data: ExaminationRecordCreate,
    appointment_service: AppointmentServiceDep,
    doctor: Doctor = Depends(get_current_doctor_profile),
):
    return await appointment_service.add_examination_record(
        appointment_id, doctor, data
    )


@appointments_router.get("/{appointment_id}/record", response_model=ExaminationOut)
async def get_appointment_record(
    appointment_service: AppointmentServiceDep,
    appointment: Appointment = Depends(get_appointment_record_access),
):
    return await appointment_service.get_appointment_record(appointment)

specialties_router = APIRouter(prefix="/specialties", tags=["Specialties"])

@specialties_router.get("", response_model=list[SpecialtyOut])
async def get_specialties(specialty_service: SpecialtyServiceDep):
    return await specialty_service.get_specialties()


@specialties_router.get("/{specialty_id}", response_model=SpecialtyOut)
async def get_specialty(specialty_id: int, specialty_service: SpecialtyServiceDep):
    try:
        return await specialty_service.get_specialty(specialty_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


doctors_router = APIRouter(prefix="/doctors", tags=["Doctors"])


@doctors_router.get("", response_model=list[DoctorOut])
async def get_doctors(
    doctor_service: DoctorServiceDep,
    specialty_id: int | None = None,
):
    return await doctor_service.get_doctors(specialty_id)


@doctors_router.get("/{doctor_id}", response_model=DoctorOut)
async def get_doctor(doctor_id: int, doctor_service: DoctorServiceDep):
    try:
        return await doctor_service.get_doctor(doctor_id)
    except ValueError as e:
        if str(e) == "Doctor not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@doctors_router.get("/{doctor_id}/schedule", response_model=DoctorScheduleOut)
async def get_doctor_schedule(doctor_id: int, doctor_service: DoctorServiceDep):
    try:
        return await doctor_service.get_doctor_schedule(doctor_id)
    except ValueError as e:
        if str(e) == "Doctor not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@doctors_router.get("/me/schedule")
async def get_my_schedule(
    doctor_service: DoctorServiceDep,
    current_user: User = Depends(check_doctor),
    response_model=list[ScheduleOut],
):
    return await doctor_service.get_my_schedule(current_user)


@doctors_router.put("/me/schedules/{schedule_id}", response_model=ScheduleOut)
async def update_my_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    doctor_service: DoctorServiceDep,
    current_doctor: User = Depends(check_doctor),
):
    try:
        return await doctor_service.update_my_schedule(
            current_doctor, schedule_id, schedule_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@doctors_router.patch("/me/schedule-slots/{slot_id}", response_model=ScheduleSlotOut)
async def update_my_schedule_slot(
    slot_data: ScheduleSlotUpdate,
    doctor_service: DoctorServiceDep,
    slot: ScheduleSlot = Depends(get_owned_schedule_slot),
):
    return await doctor_service.update_my_schedule_slot(slot, slot_data)
