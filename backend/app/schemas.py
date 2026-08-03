from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import (
    AppointmentStatus,
    Gender,
    ScheduleSlotStatus,
    ScheduleStatus,
    UserRole,
)


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: UserRole | None = None
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
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = None


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None
    phone: str | None
    avatar: str | None
    role: UserRole
    is_active: bool
    last_login: datetime | None = None
    created_date: datetime
    updated_date: datetime | None = None

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
    date_of_birth: date | None = None
    gender: Gender | None = Gender.FEMALE
    address: str | None = None
    identity_number: str | None = None
    insurance_number: str | None = None
    blood_type: str | None = None
    emergency_contact: str | None = None
    occupation: str | None = None


class PatientCreate(PatientBase):
    user_id: int = Field(..., description="ID User")


class PatientUpdate(BaseModel):
    date_of_birth: date | None = None
    gender: Gender | None = Gender.FEMALE
    address: str | None = None
    identity_number: str | None = Field(None, max_length=50)
    insurance_number: str | None = Field(None, max_length=50)
    blood_type: str | None = None
    emergency_contact: str | None = None
    occupation: str | None = None


class PatientOut(PatientBase):
    id: int
    created_date: datetime
    updated_date: datetime | None = None
    user: UserOut | None

    class Config:
        from_attributes = True


class DoctorBase(BaseModel):
    specialty_id: int
    license_number: str
    consultation_fee: Decimal = Field(..., max_digits=10, decimal_places=2)
    status: str | None = "active"
    degree: str | None = None
    experience_year: int | None = Field(None, ge=0)
    rate: float | None = Field(None, ge=0, le=5)
    biography: str | None = None


class DoctorCreate(DoctorBase):
    user_id: int = Field(..., description="ID Doctor")


class DoctorUpdate(BaseModel):
    specialty_id: int | None = None
    license_number: str | None = None
    consultation_fee: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    status: str | None = None
    degree: str | None = None
    experience_year: int | None = None
    rate: float | None = None
    biography: str | None = None


class DoctorOut(DoctorBase):
    id: int
    created_date: datetime
    updated_date: datetime | None = None
    user: UserOut | None = None
    specialty: Optional["SpecialtyOut"] = None

    class Config:
        from_attributes = True


class DoctorScheduleOut(BaseModel):
    doctor: DoctorOut
    slots: list["ScheduleSlotOut"]


class SpecialtyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    location: str | None = None
    phone: str | None = None
    email: str | None = None
    working_hours: str | None = None
    status: str | None = "active"


class SpecialtyCreate(SpecialtyBase):
    pass


class SpecialtyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    phone: str | None = None
    email: str | None = None
    working_hours: str | None = None
    status: str | None = None


class SpecialtyOut(SpecialtyBase):
    id: int
    created_date: datetime
    updated_date: datetime | None = None

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
    start_time: time | None = None
    end_time: time | None = None
    status: ScheduleSlotStatus | None = None


class ScheduleSlotOut(ScheduleSlotBase):
    id: int
    created_date: datetime
    updated_date: datetime | None = None
    start_time: datetime
    end_time: datetime
    schedule_id: int
    # appointment: Optional["AppointmentOut"] = None

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    doctor_id: int
    work_date: date
    status: ScheduleStatus = ScheduleStatus.OPEN


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    doctor_id: int | None = None
    work_date: date | None = None
    status: ScheduleStatus | None = None


class ScheduleOut(ScheduleBase):
    id: int
    created_date: datetime
    updated_date: datetime | None = None
    doctor: Optional["DoctorOut"] = None
    slots: list["ScheduleSlotOut"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AppointmentBase(BaseModel):
    slot_id: int
    reason: str | None = None
    note: str | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentCancel(BaseModel):
    cancel_reason: str


class AppointmentUpdate(BaseModel):
    reason: str | None = None
    note: str | None = None


class AppointmentOut(AppointmentBase):
    id: int
    slot_id: int
    reason: str | None
    note: str | None
    cancel_reason: str | None
    status: AppointmentStatus
    booked_at: datetime
    created_date: datetime
    patient: Optional["PatientOut"] = None
    slot: Optional["ScheduleSlotOut"] = None

    class Config:
        from_attributes = True


class MedicalRecordBase(BaseModel):
    patient_id: int
    allergy: str | None = None
    chronic_disease: str | None = None
    medical_history: str | None = None
    note: str | None = None


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecordUpdate(BaseModel):
    allergy: str | None = None
    chronic_disease: str | None = None
    medical_history: str | None = None
    note: str | None = None


class MedicalRecordOut(MedicalRecordBase):
    id: int
    created_date: datetime
    updated_date: datetime | None = None
    patient: PatientOut | None = None

    class Config:
        from_attributes = True


class ExaminationBase(BaseModel):
    appointment_id: int
    medical_record_id: int
    patient_id: int
    doctor_id: int
    symptom: str | None = None
    diagnosis: str | None = None
    conclusion: str | None = None
    disease_name: str | None = None
    height: float | None = Field(None, gt=0)
    weight: float | None = Field(None, gt=0)
    blood_pressure: str | None = None
    heart_rate: int | None = Field(None, gt=0)
    temperature: float | None = Field(None, gt=30, lt=45)
    note: str | None = None
    examined_at: datetime | None = None
    status: str | None = "in_progress"


class ExaminationCreate(ExaminationBase):
    pass


class ExaminationUpdate(BaseModel):
    appointment_id: int | None = None
    medical_record_id: int | None = None
    patient_id: int | None = None
    doctor_id: int | None = None
    symptom: str | None = None
    diagnosis: str | None = None
    conclusion: str | None = None
    disease_name: str | None = None
    height: float | None = Field(None, gt=0)
    weight: float | None = Field(None, gt=0)
    blood_pressure: str | None = None
    heart_rate: int | None = None
    temperature: float | None = None
    note: str | None = None
    examined_at: datetime | None = None
    status: str | None = None


class ExaminationOut(ExaminationBase):
    id: int
    created_date: datetime
    updated_date: datetime | None = None
    appointment: AppointmentOut | None = None
    medical_record: MedicalRecordOut | None = None
    patient: PatientOut | None = None
    doctor: DoctorOut | None = None

    class Config:
        from_attributes = True


class PrescriptionBase(BaseModel):
    examination_id: int
    prescription_type: int
    note: str | None = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionUpdate(BaseModel):
    examination_id: int | None = None
    prescription_type: int | None = None
    note: str | None = None
    status: int | None = None


class PrescriptionOut(PrescriptionBase):
    id: int
    total_amount: Decimal
    status: int
    created_date: datetime
    updated_date: datetime | None = None
    examination: ExaminationOut | None = None
    prescription_details: list["PrescriptionDetailOut"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PrescriptionDetailBase(BaseModel):
    prescription_id: int
    medicine_id: int
    quantity: int = Field(..., gt=0)
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    days: int | None = Field(None, gt=0)
    instruction: str | None = None


class PrescriptionDetailCreate(BaseModel):
    prescription_id: int
    medicine_id: int
    quantity: int = Field(..., gt=0)
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    days: int | None = Field(None, gt=0)
    instruction: str | None = None


class PrescriptionDetailUpdate(BaseModel):
    medicine_id: int | None = None
    quantity: int | None = Field(None, gt=0)
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    days: int | None = Field(None, gt=0)
    instruction: str | None = None


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
    dosage_form: str | None = None
    manufacturer: str | None = None
    current_price: Decimal = Field(..., max_digits=10, decimal_places=2)
    description: str | None = None
    stock_quantity: int = Field(..., ge=0)
    status: str = "active"


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    unit: str | None = None
    dosage_form: str | None = None
    manufacturer: str | None = None
    current_price: Decimal | None = Field(None, max_digits=10, decimal_places=2)
    description: str | None = None
    stock_quantity: int | None = Field(None, ge=0)
    status: str | None = None


class MedicineOut(MedicineBase):
    id: int
    created_date: datetime
    updated_date: datetime | None = None

    class Config:
        from_attributes = True

class PrescriptionItemCreate(BaseModel):
    medicine_id: int
    quantity: int = Field(..., gt=0)
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    days: int | None = Field(None, gt=0)
    instruction: str | None = None


class PrescriptionCreateWithoutExam(BaseModel):
    prescription_type: int
    note: str | None = None
    items: list[PrescriptionItemCreate] = []


class ExaminationRecordCreate(BaseModel):
    symptom: str | None = None
    diagnosis: str | None = None
    conclusion: str | None = None
    disease_name: str | None = None
    height: float | None = Field(None, gt=0)
    weight: float | None = Field(None, gt=0)
    blood_pressure: str | None = None
    heart_rate: int | None = Field(None, gt=0)
    temperature: float | None = Field(None, gt=30, lt=45)
    note: str | None = None
    examined_at: datetime | None = None
    prescriptions: list[PrescriptionCreateWithoutExam] | None = None

class PatientMedicalHistoryOut(BaseModel):
    medical_record: MedicalRecordOut | None = None
    examinations: list[ExaminationOut] = Field(default_factory=list)
    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    appointment_id: int
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    payment_method: str | None = None

class PaymentCreate(PaymentBase):
    pass

class PaymentOut(PaymentBase):
    id: int
    status: str
    transaction_id: str | None
    created_date: datetime
    updated_date: datetime | None

    class Config:
        from_attributes = True

DoctorOut.model_rebuild()

DoctorScheduleOut.model_rebuild()

ScheduleOut.model_rebuild()
AppointmentOut.model_rebuild()

ExaminationOut.model_rebuild()

PrescriptionDetailOut.model_rebuild()
PrescriptionOut.model_rebuild()
