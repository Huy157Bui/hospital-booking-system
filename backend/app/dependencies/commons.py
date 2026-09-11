from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.exc import InvalidTokenError
from app.dependencies.services import (
    AuthServiceDep,
    DoctorServiceDep,
    PatientServiceDep,
    ScheduleServiceDep,
    AppointmentServiceDep,
)
from app.models import User, UserRole, Doctor, Patient, Appointment, ScheduleSlot

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    auth_service: AuthServiceDep,
    token: str = Depends(oauth2_scheme),
):
    try:
        return await auth_service.get_current_user(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


def check_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403, detail="Only admin can access this resource"
        )
    return current_user


def check_doctor(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=403, detail="Only doctor can access this resource"
        )
    return current_user


def check_patient(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=403, detail="Only patient can access this resource"
        )
    return current_user


async def get_current_doctor_profile(
    doctor_service: DoctorServiceDep,
    current_user: User = Depends(check_doctor),
) -> Doctor:
    return await doctor_service.get_profile_by_user_id(current_user.id)


async def get_current_patient_profile(
    patient_service: PatientServiceDep,
    current_user: User = Depends(check_patient),
) -> Patient:
    return await patient_service.get_profile_by_user_id(current_user.id)


async def get_owned_schedule_slot(
    slot_id: int,
    schedule_service: ScheduleServiceDep,
    doctor: Doctor = Depends(get_current_doctor_profile),
) -> ScheduleSlot:
    return await schedule_service.get_owned_slot(slot_id, doctor.id)


async def get_owned_medical_record(
    patient_service: PatientServiceDep,
    patient: Patient = Depends(get_current_patient_profile),
):
    return await patient_service.get_owned_medical_record(patient.id)

async def get_appointment_record_access(
    appointment_id: int,
    appointment_service: AppointmentServiceDep,
    current_user: User = Depends(get_current_active_user),
) -> Appointment:
    return await appointment_service.get_accessible_appointment(appointment_id, current_user)