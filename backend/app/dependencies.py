from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.database import get_db
from app.models import Doctor, Patient, User, UserRole
from app.repositories import (
    DoctorRepository,
    MedicalRecordRepository,
    PatientRepository,
    ScheduleSlotRepository,
)
from app.services import AuthService

doctor_repo = DoctorRepository()
patient_repo = PatientRepository()
slot_repo = ScheduleSlotRepository()
medical_record_repo = MedicalRecordRepository()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
auth_service = AuthService()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        raise credentials_exception
    user_id = payload.get("id")
    if user_id is None:
        raise credentials_exception

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=403, detail="Only admin can access this resource"
        )
    return current_user


def get_current_doctor(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.doctor:
        raise HTTPException(
            status_code=403, detail="Only doctor can access this resource"
        )
    return current_user


def get_current_patient(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.patient:
        raise HTTPException(
            status_code=403, detail="Only patient can access this resource"
        )
    return current_user


async def get_current_doctor_profile(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_doctor)
):
    doctor = await doctor_repo.get_by_user_id(db, current_user.id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return doctor


async def get_current_patient_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
):
    patient = await patient_repo.get_by_user_id(db, current_user.id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient


async def get_owned_schedule_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile),
):
    slot = await slot_repo.get_by_id_with_schedule(db, slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="Schedule slot not found")

    if slot.schedule.doctor_id != doctor.id:
        raise HTTPException(
            status_code=403, detail="You cannot access another doctor's schedule slot"
        )
    return slot


async def get_owned_medical_record(
    db: AsyncSession = Depends(get_db),
    patient: Patient = Depends(get_current_patient_profile),
):
    medical_record = await medical_record_repo.get_by_patient_id(db, patient.id)
    if medical_record is None:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return medical_record
