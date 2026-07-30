from datetime import datetime, date, time
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from app.models import UserRole,Gender,AppointmentStatus,ScheduleStatus,ScheduleSlotStatus

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

# Update nên là partial update
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    phone: Optional[str]
    avatar: Optional[str]
    role: UserRole
    is_active: bool
    last_login: Optional[datetime] = None
    created_date: datetime
    updated_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class PatientBase(BaseModel):
    date_of_birth: Optional[date] = None
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
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = Gender.female
    address: Optional[str] = None
    identity_number: Optional[str] = Field(None, max_length=50)
    insurance_number: Optional[str] = Field(None, max_length=50)
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    occupation: Optional[str] = None

class PatientOut(PatientBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    user: Optional[UserOut]

    class Config:
        from_attributes = True

class DoctorBase(BaseModel):
    specialty_id: int
    license_number: str
    consultation_fee: Decimal = Field(..., max_digits=10, decimal_places=2)
    status: Optional[str] = "active"
    degree: Optional[str] = None
    experience_year: Optional[int] = Field(None, ge=0)
    rate: Optional[float] = Field(None, ge=0, le=5)
    biography: Optional[str] = None

class DoctorCreate(DoctorBase):
    user_id: int =  Field(..., description="ID Doctor")

class DoctorUpdate(BaseModel):
    specialty_id: Optional[int] = None
    license_number: Optional[str] = None
    consultation_fee: Optional[Decimal] = Field(None,max_digits=10,decimal_places=2)
    status: Optional[str] = None
    degree: Optional[str] = None
    experience_year: Optional[int] = None
    rate: Optional[float] = None
    biography: Optional[str] = None

class DoctorOut(DoctorBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    user: Optional[UserOut] = None
    specialty: Optional["SpecialtyOut"] = None

    class Config:
        from_attributes = True

class DoctorScheduleOut(BaseModel):
    doctor: DoctorOut
    slots: List["ScheduleSlotOut"]

class SpecialtyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    working_hours: Optional[str] = None
    status: Optional[str] = "active"

class SpecialtyCreate(SpecialtyBase):
    pass

class SpecialtyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    working_hours: Optional[str] = None
    status: Optional[str] = None

class SpecialtyOut(SpecialtyBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScheduleSlotBase(BaseModel):
    schedule_id: int
    start_time: time
    end_time: time
    status: ScheduleSlotStatus = ScheduleSlotStatus.AVAILABLE

class ScheduleSlotCreate(ScheduleSlotBase):
    pass

class ScheduleSlotUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: Optional[ScheduleSlotStatus] = None

class ScheduleSlotOut(ScheduleSlotBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    #appointment: Optional["AppointmentOut"] = None

    class Config:
        from_attributes = True

class ScheduleBase(BaseModel):
    doctor_id: int
    work_date: date
    status: ScheduleStatus = ScheduleStatus.OPEN

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    doctor_id: Optional[int] = None
    work_date: Optional[date] = None
    status: Optional[ScheduleStatus] = None

class ScheduleOut(ScheduleBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    doctor: Optional["DoctorOut"] = None
    slots: List["ScheduleSlotOut"] = Field(default_factory=list)
    class Config:
        from_attributes = True

class AppointmentBase(BaseModel):
    patient_id: int
    slot_id: int
    reason: Optional[str] = None
    note: Optional[str] = None
    cancel_reason: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.pending

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    patient_id: Optional[int] = None
    slot_id: Optional[int] = None
    reason: Optional[str] = None
    note: Optional[str] = None
    cancel_reason: Optional[str] = None
    status: Optional[AppointmentStatus] = None

class AppointmentOut(AppointmentBase):
    id: int
    booked_at: datetime
    created_date: datetime
    patient: Optional["PatientOut"] = None
    slot: Optional["ScheduleSlotOut"] = None
    class Config:
        from_attributes = True

class MedicalRecordBase(BaseModel):
    patient_id: int
    allergy: Optional[str] = None
    chronic_disease: Optional[str] = None
    medical_history: Optional[str] = None
    note: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordUpdate(BaseModel):
    allergy: Optional[str] = None
    chronic_disease: Optional[str] = None
    medical_history: Optional[str] = None
    note: Optional[str] = None

class MedicalRecordOut(MedicalRecordBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    patient: Optional[PatientOut] = None

    class Config:
        from_attributes = True

class ExaminationBase(BaseModel):
    appointment_id: int
    medical_record_id: int
    patient_id: int
    doctor_id: int
    symptom: Optional[str] = None
    diagnosis: Optional[str] = None
    conclusion: Optional[str] = None
    disease_name: Optional[str] = None
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = Field(None, gt=0)
    temperature: Optional[float] = Field(None, gt=30, lt=45)
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
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
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

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionUpdate(BaseModel):
    examination_id: Optional[int] = None
    prescription_type: Optional[int] = None
    note: Optional[str] = None
    status: Optional[int] = None

class PrescriptionOut(PrescriptionBase):
    id: int
    total_amount: Decimal
    status: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    examination: Optional[ExaminationOut] = None
    prescription_details: List["PrescriptionDetailOut"] = Field(default_factory=list)

    class Config:
        from_attributes = True

class PrescriptionDetailBase(BaseModel):
    prescription_id: int
    medicine_id: int
    quantity: int = Field(..., gt=0)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    days: Optional[int] = Field(None, gt=0)
    instruction: Optional[str] = None

class PrescriptionDetailCreate(BaseModel):
    prescription_id: int
    medicine_id: int
    quantity: int = Field(..., gt=0)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    days: Optional[int] = Field(None, gt=0)
    instruction: Optional[str] = None

class PrescriptionDetailUpdate(BaseModel):
    medicine_id: Optional[int] = None
    quantity: Optional[int] = Field(None, gt=0)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    days: Optional[int] = Field(None, gt=0)
    instruction: Optional[str] = None

class PrescriptionDetailOut(PrescriptionDetailBase):
    id: int
    unit_price: Decimal
    subtotal: Decimal
    medicine: Optional["MedicineOut"] = None

    class Config:
        from_attributes = True

class MedicineBase(BaseModel):
    name: str
    code: str
    unit: str
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None
    current_price: Decimal = Field(..., max_digits=10, decimal_places=2)
    description: Optional[str] = None
    stock_quantity: int = Field(..., ge=0)
    status: str = "active"

class MedicineCreate(MedicineBase):
    pass

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    unit: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None
    current_price: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    description: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None

class MedicineOut(MedicineBase):
    id: int
    created_date: datetime
    updated_date: Optional[datetime] = None
    class Config:
        from_attributes = True

# chứa forward reference
DoctorOut.model_rebuild()

DoctorScheduleOut.model_rebuild()

ScheduleOut.model_rebuild()
AppointmentOut.model_rebuild()

ExaminationOut.model_rebuild()

PrescriptionDetailOut.model_rebuild()
PrescriptionOut.model_rebuild()