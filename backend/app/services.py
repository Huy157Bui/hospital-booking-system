from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core import settings
from app.models import (
    Appointment,
    Doctor,
    Patient,
    ScheduleSlot,
    ScheduleSlotStatus,
    Specialty,
    User,
    UserRole,
)
from app.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
    ScheduleRepository,
    ScheduleSlotRepository,
    SpecialtyRepository,
    UserRepository,
)
from app.schemas import (
    AppointmentCreate,
    DoctorCreate,
    ScheduleSlotUpdate,
    SpecialtyCreate,
    SpecialtyUpdate,
    UserCreate,
)

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

    def register(self, db: Session, user_data: UserCreate) -> User:
        if self.repo.get_by_username(db, user_data.username):
            raise ValueError("Username already exists")
        if self.repo.get_by_email(db, user_data.email):
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
        return self.repo.create(db, user)

    def authenticate(self, db: Session, username: str, password: str) -> User | None:
        user = self.repo.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def login(self, db: Session, username: str, password: str) -> dict | None:
        user = self.authenticate(db, username, password)
        if not user:
            raise ValueError("Invalid username or password")
        if not user.is_active:
            raise ValueError("Account is inactive")

        user.last_login = datetime.now(UTC)
        self.repo.update(db, user)

        access_token = create_access_token(
            data={"sub": user.username, "id": user.id, "role": user.role.value}
        )
        return {"access_token": access_token, "token_type": "bearer", "user": user}

    def get_user_by_username(self, db: Session, username: str) -> User | None:
        user = self.repo.get_by_username(db, username)
        if user is None:
            return None
        if not user.is_active:
            return None
        return user

    def get_user_by_id(self, db: Session, user_id: int) -> User | None:
        user = self.repo.get_by_id(db, user_id)
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

    def get_user_appointments(
        self, db: Session, current_user: User
    ) -> list[Appointment]:
        if current_user.role == UserRole.patient:
            return self.repo.get_by_patient(db, current_user.id)
        return self.repo.get_by_doctor(db, current_user.id)

    def create_appointment(
        self,
        db: Session,
        patient: Patient,
        appointment_data: AppointmentCreate,
    ):
        slot = self.slot_repo.get_by_id(
            db,
            appointment_data.slot_id,
        )
        if slot is None:
            raise ValueError("Schedule slot not found")
        if slot.status != ScheduleSlotStatus.AVAILABLE:
            raise ValueError("Schedule slot is unavailable")
        if slot.appointment is not None:
            raise ValueError("Schedule slot has already been booked")
        appointment = self.repo.get_by_slot_id(db, appointment_data.slot_id)
        if appointment is not None:
            raise ValueError("Schedule slot has already been booked")

    def get_appointment_detail(
        self, db: Session, appointment_id: int, current_user: User
    ):
        appointment = self.repo.get_by_id_with_relations(db, appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        if current_user.role == UserRole.admin:
            return appointment
        if current_user.role == UserRole.patient:
            patient = self.patient_repo.get_by_user_id(db, current_user.id)
            if not patient or appointment.patient_id != patient.id:
                raise ValueError("Access denied")
            return appointment
        if current_user.role == UserRole.doctor:
            doctor = self.doctor_repo.get_by_user_id(db, current_user.id)
            if not doctor or appointment.slot.schedule.doctor_id != doctor.id:
                raise ValueError("Access denied")
            return appointment

        raise ValueError("Invalid role")


class SpecialtyService:
    def __init__(self):
        self.repo = SpecialtyRepository()
        self.doctor_repo = DoctorRepository()

    def get_specialties(self, db: Session) -> list[Specialty]:
        return self.repo.get_active_specialties(db)

    def get_specialty(self, db: Session, specialty_id: int) -> Specialty:
        specialty = self.repo.get_active_by_id(db, specialty_id)
        if specialty is None:
            raise ValueError("Specialty not found")
        return specialty

    # tao chuyen khoa
    def create_specialty(
        self, db: Session, specialty_data: SpecialtyCreate
    ) -> Specialty:
        existed = self.repo.get_by_name(db, specialty_data.name)
        if existed:
            raise ValueError("Specialty already exists")
        specialty = Specialty(**specialty_data.model_dump())
        return self.repo.create(db, specialty)

    def toggle_specialty_status(self, db: Session, specialty_id: int) -> Specialty:
        specialty = self.repo.get_by_id(db, specialty_id)
        if specialty is None:
            raise ValueError("Specialty not found")
        return self.repo.toggle_status(db, specialty)

    def update_specialty(
        self, db: Session, specialty_id: int, specialty_data: SpecialtyUpdate
    ) -> Specialty:
        specialty = self.repo.get_active_by_id(db, specialty_id)
        if specialty is None:
            raise ValueError("Specialty not found")
        if specialty_data.name and specialty_data.name != specialty.name:
            existed = self.repo.get_by_name(db, specialty_data.name)
            if existed:
                raise ValueError("Specialty already exists")

        update_data = specialty_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(specialty, field, value)
        return self.repo.update(db, specialty)


class DoctorService:
    def __init__(self):
        self.repo = DoctorRepository()
        self.user_repo = UserRepository()
        self.specialty_repo = SpecialtyRepository()
        self.schedule_repo = ScheduleRepository()
        self.appointment_repo = AppointmentRepository()
        self.slot_repo = ScheduleSlotRepository()

    def get_doctors(self, db: Session, specialty_id: int | None = None) -> list[Doctor]:
        if specialty_id is None:
            return self.repo.get_active_doctors(db)
        return self.repo.get_by_specialty(db, specialty_id)

    def get_doctor(self, db: Session, doctor_id: int) -> Doctor:
        doctor = self.repo.get_active_by_id(db, doctor_id)
        if doctor is None:
            raise ValueError("Doctor not found")
        return doctor

    def get_doctor_schedule(self, db: Session, doctor_id: int):
        doctor = self.repo.get_active_by_id(db, doctor_id)
        if doctor is None:
            raise ValueError("Doctor not found")
        schedules = self.schedule_repo.get_by_doctor(db, doctor_id)
        return schedules

    def update_my_schedule_slot(
        self,
        db: Session,
        slot: ScheduleSlot,
        slot_data: ScheduleSlotUpdate,
    ):
        if slot.status == ScheduleSlotStatus.BOOKED:
            raise ValueError("Booked slots cannot be modified")
        update_data = slot_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(slot, field, value)
        return self.slot_repo.update(db, slot)

    def create_doctor(self, db: Session, doctor_data: DoctorCreate):
        user = self.user_repo.get_by_id(db, doctor_data.user_id)
        if user is None:
            raise ValueError("User not found")
        if user.role != UserRole.doctor:
            raise ValueError("User is not a doctor")
        if self.repo.get_by_user_id(db, doctor_data.user_id):
            raise ValueError("Doctor profile already exists")
        specialty = self.specialty_repo.get_active_by_id(db, doctor_data.specialty_id)
        if specialty is None:
            raise ValueError("Specialty not found")
        if self.repo.get_by_license(db, doctor_data.license_number):
            raise ValueError("License already exists")
        doctor = Doctor(
            id=doctor_data.user_id, **doctor_data.model_dump(exclude={"user_id"})
        )
        return self.repo.create(db, doctor)
