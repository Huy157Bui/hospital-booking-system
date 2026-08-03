from datetime import UTC, datetime, timedelta, date

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import DECIMAL
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    Patient,
    ScheduleSlot,
    ScheduleSlotStatus,
    Specialty,
    User,
    UserRole,
Medicine, MedicalRecord, Examination, PrescriptionDetail, Prescription
)
from app.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
    ScheduleRepository,
    ScheduleSlotRepository,
    SpecialtyRepository,
    UserRepository,
    MedicalRecordRepository,
    ExaminationRepository,
    PrescriptionRepository,
    PrescriptionDetailRepository,
    MedicineRepository,
)
from app.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    DoctorCreate,
    ScheduleSlotUpdate,
    SpecialtyCreate,
    SpecialtyUpdate,
    UserCreate,
    ExaminationRecordCreate,
)
from app.utils import generate_record_number

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


class AuthService:
    def __init__(self):
        self.repo = UserRepository()

    async def register(self, db: AsyncSession, user_data: UserCreate) -> User:
        if await self.repo.get_by_username(db, user_data.username):
            raise ValueError("Username already exists")
        if await self.repo.get_by_email(db, user_data.email):
            raise ValueError("Email already exists")

        hashed_password = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            phone=user_data.phone,
            avatar=user_data.avatar,
            role=user_data.role or UserRole.patient,
            is_active=True,
            password=hashed_password,
        )
        return await self.repo.create(db, user)

    async def authenticate(
        self, db: AsyncSession, username: str, password: str
    ) -> User | None:
        user = await self.repo.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    async def login(
        self, db: AsyncSession, username: str, password: str
    ) -> dict | None:
        user = await self.authenticate(db, username, password)
        if not user:
            raise ValueError("Invalid username or password")
        if not user.is_active:
            raise ValueError("Account is inactive")

        user.last_login = datetime.now(UTC)
        await self.repo.update(db, user)

        access_token = create_access_token(
            data={"sub": user.username, "id": user.id, "role": user.role.value}
        )
        return {"access_token": access_token, "token_type": "bearer", "user": user}

    async def get_user_by_username(
        self, db: AsyncSession, username: str
    ) -> User | None:
        user = await self.repo.get_by_username(db, username)
        if user is None:
            return None
        if not user.is_active:
            return None
        return user

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        user = await self.repo.get_by_id(db, user_id)
        if user is None:
            return None
        if not user.is_active:
            return None
        return user


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    def get_profile(self, current_user: User):
        return current_user


class AppointmentService:
    def __init__(self):
        self.repo = AppointmentRepository()
        self.slot_repo = ScheduleSlotRepository()
        self.doctor_repo = DoctorRepository()
        self.patient_repo = PatientRepository()
        self.medical_record_repo = MedicalRecordRepository()
        self.examination_repo = ExaminationRepository()
        self.prescription_repo = PrescriptionRepository()
        self.prescription_detail_repo = PrescriptionDetailRepository()
        self.medicine_repo = MedicineRepository()

    async def get_user_appointments(
        self, db: AsyncSession, current_user: User
    ) -> list[Appointment]:
        if current_user.role == UserRole.patient:
            return await self.repo.get_by_patient(db, current_user.id)
        return await self.repo.get_by_doctor(db, current_user.id)

    async def create_appointment(
        self,
        db: AsyncSession,
        patient: Patient,
        appointment_data: AppointmentCreate,
    ):
        slot = await self.slot_repo.get_by_id(db, appointment_data.slot_id)
        if slot is None:
            raise ValueError("Schedule slot not found")
        if slot.status != ScheduleSlotStatus.AVAILABLE:
            raise ValueError("Schedule slot is unavailable")
        if slot.appointment is not None:
            raise ValueError("Schedule slot has already been booked")
        existing = await self.repo.get_by_slot_id(db, appointment_data.slot_id)
        if existing is not None:
            raise ValueError("Schedule slot has already been booked")

    async def get_appointment_detail(
        self, db: AsyncSession, appointment_id: int, current_user: User
    ):
        appointment = await self.repo.get_by_id_with_relations(db, appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        if current_user.role == UserRole.admin:
            return appointment
        if current_user.role == UserRole.patient:
            patient = await self.patient_repo.get_by_user_id(db, current_user.id)
            if not patient or appointment.patient_id != patient.id:
                raise ValueError("Access denied")
            return appointment
        if current_user.role == UserRole.doctor:
            doctor = await self.doctor_repo.get_by_user_id(db, current_user.id)
            if not doctor or appointment.slot.schedule.doctor_id != doctor.id:
                raise ValueError("Access denied")
            return appointment

        raise ValueError("Invalid role")

    async def cancel_appointment(
        self,
        db: AsyncSession,
        appointment_id: int,
        current_user: User,
        cancel_data: AppointmentCancel,
    ):
        appointment = await self.repo.get_by_id_with_slot(db, appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")

        if current_user.role != UserRole.admin:
            if current_user.role != UserRole.patient:
                raise ValueError("Access denied")
            patient = await self.patient_repo.get_by_user_id(db, current_user.id)
            if not patient or appointment.patient_id != patient.id:
                raise ValueError("Access denied")

        if appointment.status == AppointmentStatus.CANCELLED:
            raise ValueError("Appointment is already cancelled")
        if appointment.status == AppointmentStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed appointment")

        return await self.repo.cancel(db, appointment, cancel_data.cancel_reason)

    async def update_appointment_status(
        self,
        db: AsyncSession,
        appointment_id: int,
        new_status: AppointmentStatus,
        current_user: User,
        doctor: Doctor,
    ) -> Appointment:

        appointment = await self.repo.get_by_id_with_slot(db, appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")

        if appointment.slot.schedule.doctor_id != doctor.id:
            raise ValueError("You are not the doctor assigned to this appointment")

        current_status = appointment.status
        if current_status in (
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.PAID,
        ):
            raise ValueError(f"Cannot change status from {appointment.status.value}")

        valid_transitions = {
            AppointmentStatus.PENDING: [
                AppointmentStatus.CHECKING_IN,
                AppointmentStatus.EXAMINING,
            ],
            AppointmentStatus.CONFIRMED: [
                AppointmentStatus.CHECKING_IN,
                AppointmentStatus.EXAMINING,
            ],
            AppointmentStatus.CHECKING_IN: [
                AppointmentStatus.EXAMINING,
                AppointmentStatus.COMPLETED,
            ],
            AppointmentStatus.EXAMINING: [AppointmentStatus.COMPLETED],
        }
        allowed = valid_transitions.get(current_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Can only transition from {current_status.value} to one of {[s.value for s in allowed]}"
            )
        await self.repo.update_status(db, appointment, new_status)
        updated = await self.repo.get_by_id_with_relations(db, appointment_id)
        if not updated:
            raise ValueError("Appointment not found after update")
        return updated

    async def get_available_slots(
        self, db: AsyncSession, doctor_id: int, date: date
    ) -> list[ScheduleSlot]:
        slots = await self.slot_repo.get_available_slots_by_doctor_and_date(
            db, doctor_id, date
        )
        return slots

    async def add_examination_record(
        self,
        db: AsyncSession,
        appointment_id: int,
        doctor: Doctor,
        data: ExaminationRecordCreate,
    ) -> Examination:
        appointment = await self.repo.get_by_id_with_slot(db, appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        if appointment.slot.schedule.doctor_id != doctor.id:
            raise ValueError("You are not the assigned doctor")

        if appointment.status not in (AppointmentStatus.EXAMINING, AppointmentStatus.COMPLETED):
            raise ValueError("Cannot add record for this status")

        patient = appointment.patient
        if not patient:
            raise ValueError("Patient not found")

        medical_record = await self.medical_record_repo.get_by_patient_id(db, patient.id)
        if not medical_record:
            record_number = generate_record_number()
            medical_record = MedicalRecord(
                patient_id=patient.id,
                record_number=record_number,
            )
            db.add(medical_record)
            await db.flush()

        examination = await self.examination_repo.get_by_appointment(db, appointment_id)
        if not examination:
            examination = Examination(
                appointment_id=appointment_id,
                medical_record_id=medical_record.id,
                patient_id=patient.id,
                doctor_id=doctor.id,
                symptom=data.symptom,
                diagnosis=data.diagnosis,
                conclusion=data.conclusion,
                disease_name=data.disease_name,
                height=data.height,
                weight=data.weight,
                blood_pressure=data.blood_pressure,
                heart_rate=data.heart_rate,
                temperature=data.temperature,
                note=data.note,
                examined_at=data.examined_at or datetime.now(UTC),
                status="completed" if appointment.status == AppointmentStatus.COMPLETED else "in_progress",
            )
            db.add(examination)
            await db.flush()
        else:
            examination.symptom = data.symptom
            examination.diagnosis = data.diagnosis
            examination.conclusion = data.conclusion
            examination.disease_name = data.disease_name
            examination.height = data.height
            examination.weight = data.weight
            examination.blood_pressure = data.blood_pressure
            examination.heart_rate = data.heart_rate
            examination.temperature = data.temperature
            examination.note = data.note
            examination.examined_at = data.examined_at or datetime.now(UTC)
            if appointment.status == AppointmentStatus.COMPLETED:
                examination.status = "completed"

        if data.prescriptions:
            existing_prescriptions = await self.prescription_repo.get_by_examination(db, examination.id)
            for old_pres in existing_prescriptions:
                await db.delete(old_pres)
            await db.flush()

            for pres_data in data.prescriptions:
                prescription = Prescription(
                    examination_id=examination.id,
                    prescription_type=pres_data.prescription_type,
                    note=pres_data.note,
                    total_amount=DECIMAL(0),
                    status=0,
                )
                db.add(prescription)
                await db.flush()

                total = DECIMAL(0)
                for item in pres_data.items:
                    medicine = await self.medicine_repo.get_by_id(db, item.medicine_id)
                    if not medicine:
                        raise ValueError(f"Medicine {item.medicine_id} not found")
                    unit_price = medicine.current_price
                    subtotal = unit_price * item.quantity
                    total += subtotal

                    detail = PrescriptionDetail(
                        prescription_id=prescription.id,
                        medicine_id=item.medicine_id,
                        quantity=item.quantity,
                        unit_price=unit_price,
                        dosage=item.dosage,
                        frequency=item.frequency,
                        duration=item.duration,
                        days=item.days,
                        instruction=item.instruction,
                        subtotal=subtotal,
                    )
                    db.add(detail)

                prescription.total_amount = total

        await db.commit()
        await db.refresh(examination)
        return examination

class SpecialtyService:
    def __init__(self):
        self.repo = SpecialtyRepository()
        self.doctor_repo = DoctorRepository()

    async def get_specialties(self, db: AsyncSession) -> list[Specialty]:
        return await self.repo.get_active_specialties(db)

    async def get_specialty(self, db: AsyncSession, specialty_id: int) -> Specialty:
        specialty = await self.repo.get_active_by_id(db, specialty_id)
        if specialty is None:
            raise ValueError("Specialty not found")
        return specialty

    async def create_specialty(
        self, db: AsyncSession, specialty_data: SpecialtyCreate
    ) -> Specialty:
        existed = await self.repo.get_by_name(db, specialty_data.name)
        if existed:
            raise ValueError("Specialty already exists")
        specialty = Specialty(**specialty_data.model_dump())
        return await self.repo.create(db, specialty)

    async def toggle_specialty_status(
        self, db: AsyncSession, specialty_id: int
    ) -> Specialty:
        specialty = await self.repo.get_by_id(db, specialty_id)
        if specialty is None:
            raise ValueError("Specialty not found")
        return await self.repo.toggle_status(db, specialty)

    async def update_specialty(
        self, db: AsyncSession, specialty_id: int, specialty_data: SpecialtyUpdate
    ) -> Specialty:
        specialty = await self.repo.get_active_by_id(db, specialty_id)
        if specialty is None:
            raise ValueError("Specialty not found")
        if specialty_data.name and specialty_data.name != specialty.name:
            existed = await self.repo.get_by_name(db, specialty_data.name)
            if existed:
                raise ValueError("Specialty already exists")

        update_data = specialty_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(specialty, field, value)
        return await self.repo.update(db, specialty)


class DoctorService:
    def __init__(self):
        self.repo = DoctorRepository()
        self.user_repo = UserRepository()
        self.specialty_repo = SpecialtyRepository()
        self.schedule_repo = ScheduleRepository()
        self.appointment_repo = AppointmentRepository()
        self.slot_repo = ScheduleSlotRepository()

    async def get_doctors(
        self, db: AsyncSession, specialty_id: int | None = None
    ) -> list[Doctor]:
        if specialty_id is None:
            return await self.repo.get_active_doctors(db)
        return await self.repo.get_by_specialty(db, specialty_id)

    async def get_doctor(self, db: AsyncSession, doctor_id: int) -> Doctor:
        doctor = await self.repo.get_active_by_id(db, doctor_id)
        if doctor is None:
            raise ValueError("Doctor not found")
        return doctor

    async def get_doctor_schedule(self, db: AsyncSession, doctor_id: int):
        doctor = await self.repo.get_active_by_id(db, doctor_id)
        if doctor is None:
            raise ValueError("Doctor not found")
        schedules = await self.schedule_repo.get_by_doctor(db, doctor_id)
        return schedules

    async def update_my_schedule_slot(
        self,
        db: AsyncSession,
        slot: ScheduleSlot,
        slot_data: ScheduleSlotUpdate,
    ):
        if slot.status == ScheduleSlotStatus.BOOKED:
            raise ValueError("Booked slots cannot be modified")
        update_data = slot_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(slot, field, value)
        return await self.slot_repo.update(db, slot)

    async def create_doctor(self, db: AsyncSession, doctor_data: DoctorCreate):
        user = await self.user_repo.get_by_id(db, doctor_data.user_id)
        if user is None:
            raise ValueError("User not found")
        if user.role != UserRole.doctor:
            raise ValueError("User is not a doctor")
        if await self.repo.get_by_user_id(db, doctor_data.user_id):
            raise ValueError("Doctor profile already exists")
        specialty = await self.specialty_repo.get_active_by_id(
            db, doctor_data.specialty_id
        )
        if specialty is None:
            raise ValueError("Specialty not found")
        if await self.repo.get_by_license(db, doctor_data.license_number):
            raise ValueError("License already exists")
        doctor = Doctor(
            id=doctor_data.user_id, **doctor_data.model_dump(exclude={"user_id"})
        )
        return await self.repo.create(db, doctor)
