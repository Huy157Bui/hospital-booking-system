from datetime import datetime, date, time
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from app.models import UserRole, Gender

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: bool = True

class UserCreate(UserBase):
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: bool = True
    password: Optional[str] = None


class UserOut(BaseModel):
    id: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatientBase(BaseModel):
    date_of_birth: Optional[datetime] = None
    gender: Optional[Gender] = Gender.female
    address: Optional[str] = None
    identity_number: Optional[str] = None
    insurance_number: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    occupation: Optional[str] = None

class PatientCreate(PatientBase):
    user_id: int = Field(..., description="ID User")

class PatientUpdate(BaseModel):
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Gender.female
    address: Optional[str] = None
    identity_number: Optional[str] = None
    insurance_number: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    occupation: Optional[str] = None

class PatientOut(PatientBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: Optional[UserOut] = None

    class Config:
        from_attributes = True

#patientIn

class DoctorBase(BaseModel):
    specialty_id: int
    license: str
    consultation_fee: Decimal = Field(..., max_digits=10, decimal_places=2)
    status: Optional[str] = "active"
    degree: Optional[str] = None
    experience_year: Optional[str] = None
    rate: Optional[float] = None
    biography: Optional[str] = None

class DoctorCreate(DoctorBase):
    user_id: int =  Field(..., description="ID Doctor")

class DoctorUpdate(DoctorBase):
    specialty_id: int
    license: str
    consultation_fee: Decimal = Field(..., max_digits=10, decimal_places=2)
    status: Optional[str] = "active"
    degree: Optional[str] = None
    experience_year: Optional[str] = None
    rate: Optional[float] = None
    biography: Optional[str] = None

class DoctorOut(DoctorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserOut] = None
    specialty: Optional[int] = None

    class Config:
        from_attributes = True

class SpecialtyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    work_hours: Optional[str] = None
    status: Optional[str] = "active"

class SpecialtyCreate(SpecialtyBase):
    pass

class SpecialtyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    work_hours: Optional[str] = None
    status: Optional[str] = None

class SpecialtyOut(SpecialtyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScheduleBase(BaseModel):
    doctor_id: int
    work_date: date
    start_date: time
    end_date: time
    max_patients: int = Field(10, ge=1)
    status: Optional[str] = "available"

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    doctor_id: Optional[int] = None
    work_date: Optional[date] = None
    start_date: Optional[time] = None
    end_date: Optional[time] = None
    max_patients: Optional[int] = None
    status: Optional[str] = None

class ScheduleOut(ScheduleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    doctor: Optional[DoctorOut] = None

    class Config:
        from_attributes = True

class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    schedule_id: int
    appointment_date: Optional[date] = None
    reason: Optional[str] = None
    note: Optional[str] = None
    cancel_reason: Optional[str] = None
    status: Optional[str] = "pending"

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(AppointmentBase):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    schedule_id: Optional[int] = None
    appointment_date: Optional[datetime] = None
    reason: Optional[str] = None
    note: Optional[str] = None
    cancel_reason: Optional[str] = None
    status: Optional[str] = None

class AppointmentOut(AppointmentBase):
    id: int
    created_at: datetime
    patient: Optional[PatientOut] = None
    doctor: Optional[DoctorOut] = None
    schedule: Optional[ScheduleOut] = None

    class Config:
        from_attributes = True

class MedicalRecordBase(BaseModel):
    patient_id: int
    record_number: Optional[str] = None
    allergy: Optional[str] = None
    chronic_disease: Optional[str] = None
    medical_history: Optional[str] = None
    note: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordUpdate(BaseModel):
    record_number: Optional[str] = None
    allergy: Optional[str] = None
    chronic_disease: Optional[str] = None
    medical_history: Optional[str] = None
    note: Optional[str] = None

class MedicalRecordOut(MedicalRecordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    patient: Optional[PatientOut] = None

    class Config:
        from_attributes = True

class ExaminationBase(BaseModel):
    appointment_id: int
    medical_record: int
    patient_id: int
    doctor_id: int
    symptom: Optional[str] = None
    diagnosis: Optional[str] = None
    conclusion: Optional[str] = None
    disease_name: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    note: Optional[str] = None
    examined_at: Optional[datetime] = None
    status: Optional[str] = "in_progress"

class ExaminationCreate(ExaminationBase):
    pass

class ExaminationUpdate(BaseModel):
    appointment_id: Optional[int] = None
    medical_record_id: Optional[int] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    symptom: Optional[str] = None
    diagnosis: Optional[str] = None
    conclusion: Optional[str] = None
    disease_name: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    note: Optional[str] = None
    examined_at: Optional[datetime] = None
    status: Optional[str] = None

class ExaminationOut(ExaminationBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    appointment: Optional[AppointmentOut] = None
    medical_record: Optional[MedicalRecordOut] = None
    patient: Optional[PatientOut] = None
    doctor: Optional[DoctorOut] = None

    class Config:
        from_attributes = True

class PrescriptionBase(BaseModel):
    examination_id: int
    prescription_type: int
    note: Optional[str] = None
    total_amount: Optional[Decimal] = Field(0, max_digits=12, decimal_places=2)
    status: Optional[int] = 0

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionUpdate(BaseModel):
    examination_id: Optional[int] = None
    prescription_type: Optional[int] = None
    note: Optional[str] = None
    total_amount: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    status: Optional[int] = None

class PrescriptionDetailOut(BaseModel):
    id: int
    medicine_id: int
    quantity: int
    unit_price: Decimal
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    days: Optional[int] = None
    instruction: Optional[str] = None
    subtotal: Decimal

    class Config:
        from_attributes = True

class PrescriptionOut(PrescriptionBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    examination: Optional[ExaminationOut] = None
    prescription_details: Optional[List["PrescriptionDetailOut"]] = None

    class Config:
        from_attributes = True













