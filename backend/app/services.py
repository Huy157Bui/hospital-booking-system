import asyncio
import json
import logging
import re
import unicodedata
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.utils import embedding_functions
from jose import JWTError, jwt
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, ValidationError
from passlib.context import CryptContext
from passlib.exc import InvalidTokenError

from app.core import settings
from app.dependencies.repos import (
    ChatMessageRepoDep,
    ChatSessionRepoDep,
    AppointmentRepoDep,
    DoctorRepoDep,
    ExaminationRepoDep,
    MedicalRecordRepoDep,
    MedicineRepoDep,
    PatientRepoDep,
    PaymentRepoDep,
    PrescriptionDetailRepoDep,
    PrescriptionRepoDep,
    ReportRepoDep,
    ScheduleRepoDep,
    ScheduleSlotRepoDep,
    SpecialtyRepoDep,
    UserRepoDep,
)
from app.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    ResourceNotFound,
)
from app.models import (
    ChatMessage,
    ChatSession,
    Appointment,
    AppointmentStatus,
    Doctor,
    Examination,
    MedicalRecord,
    Medicine,
    Patient,
    Payment,
    PaymentStatus,
    Prescription,
    PrescriptionDetail,
    ScheduleSlot,
    ScheduleSlotStatus,
    Specialty,
    User,
    UserRole,
    RefreshToken,
    Gender,
)
from app.repositories import RefreshTokenRepository
from app.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentsSummaryResponse,
    AppointmentStatusCount,
    DailyAppointmentSummary,
    DoctorCreate,
    ExaminationRecordCreate,
    PatientsBySpecialtyItem,
    PatientsBySpecialtyResponse,
    PaymentOut,
    RevenueItem,
    RevenueResponse,
    ScheduleSlotUpdate,
    SpecialtyCreate,
    SpecialtyUpdate,
    UserCreate,
    UserUpdate,
    ScheduleSlotOut,
    AppointmentAvailabilityQuery,
    CheckAvailabilityInput,
    SearchDoctorsInput,
    ListSpecialtiesInput,
    BookAppointmentInput,
    PatientUpdate,
    SearchKnowledgeInput,
    ScheduleOut
)
from app.schemas import PatientSummaryOut
from app.utils import generate_record_number

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent.parent
CHROMA_DB_DIR = PROJECT_ROOT / "database" / "chroma_db"

if not CHROMA_DB_DIR.exists():
    CHROMA_DB_DIR = CURRENT_FILE.parent.parent / "database" / "chroma_db"

COLLECTION_NAME = "bachmai_knowledge"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

class AuthService:
    def __init__(
        self,
        user_repo: UserRepoDep,
        patient_repo: PatientRepoDep,
        refresh_token_repo: RefreshTokenRepository,
    ):
        self.user_repo = user_repo
        self.patient_repo = patient_repo
        self.refresh_token_repo = refresh_token_repo

    def _decode_and_verify_type(self, token: str, expected_type: str) -> dict:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except jwt.JWTError:
            raise InvalidTokenError("Invalid token")
        if payload.get("type", "access") != expected_type:
            raise InvalidTokenError("Invalid token type")
        return payload

    def decode_token(self, token: str) -> int:
        payload = self._decode_and_verify_type(token, "access")
        user_id = payload.get("id")
        if user_id is None:
            raise InvalidTokenError("Invalid token payload")
        return user_id


    async def create_refresh_token(self, user: User) -> str:
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        record = await self.refresh_token_repo.create(
            RefreshToken(user_id=user.id, expires_at=expire, revoked=False)
        )
        return jwt.encode(
            {
                "sub": user.username,
                "id": user.id,
                "jti": record.id,
                "type": "refresh",
                "exp": expire,
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    async def get_current_user(self, token: str) -> User:
        user_id = self.decode_token(token)
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError("User not found")
        return user

    async def register(self, user_data: UserCreate) -> User:
        if await self.user_repo.get_by_username(user_data.username):
            raise BadRequestException("Tên đăng nhập đã tồn tại")
        if await self.user_repo.get_by_email(user_data.email):
            raise BadRequestException("Email đã tồn tại")

        hashed_password = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            phone=user_data.phone,
            avatar=user_data.avatar,
            role=user_data.role or UserRole.PATIENT,
            is_active=True,
            password=hashed_password,
        )
        created_user = await self.user_repo.create(user)

        if created_user.role == UserRole.PATIENT:
            patient = Patient(
                id=created_user.id,
                gender=Gender.FEMALE,
            )
            await self.patient_repo.create(patient)
            await self.patient_repo.commit()

        return created_user

    async def authenticate(self, username: str, password: str) -> User | None:
        user = await self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.password):
            return None
        return user

    async def login(self, username: str, password: str) -> dict | None:
        user = await self.authenticate(username, password)
        if not user:
            raise BadRequestException("Sai tên đăng nhập hoặc mật khẩu")
        if not user.is_active:
            raise ForbiddenException("Tài khoản bị vô hiệu hóa")

        user.last_login = datetime.now(UTC)
        await self.user_repo.update(user)

        access_token = create_access_token(
            data={
                "sub": user.username,
                "id": user.id,
                "role": user.role.value,
                "type": "access",
            }
        )
        refresh_token = await self.create_refresh_token(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    async def get_user_by_username(self, username: str) -> User | None:
        user = await self.user_repo.get_by_username(username)
        if user is None or not user.is_active:
            return None
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            return None
        return user

    async def refresh_access_token(self, refresh_token_str: str) -> dict:
        payload = self._decode_and_verify_type(refresh_token_str, "refresh")
        jti, user_id = payload.get("jti"), payload.get("id")
        if jti is None or user_id is None:
            raise InvalidTokenError("Invalid token payload")

        record = await self.refresh_token_repo.get_by_id(jti)
        if record is None or record.revoked or record.expires_at < datetime.now(UTC):
            raise InvalidTokenError("Invalid or expired refresh token")

        user = await self.user_repo.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise InvalidTokenError("User not found or inactive")

        await self.refresh_token_repo.revoke(record)
        new_refresh_token = await self.create_refresh_token(user)
        new_access_token = create_access_token(
            data={
                "sub": user.username,
                "id": user.id,
                "role": user.role.value,
                "type": "access",
            }
        )
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout(self, refresh_token_str: str) -> None:
        payload = self._decode_and_verify_type(refresh_token_str, "refresh")
        jti = payload.get("jti")
        if jti is None:
            raise InvalidTokenError("Invalid token payload")
        record = await self.refresh_token_repo.get_by_id(jti)
        if record and not record.revoked:
            await self.refresh_token_repo.revoke(record)

    async def change_password(
        self, current_user: User, old_password: str, new_password: str
    ) -> None:
        if not verify_password(old_password, current_user.password):
            raise BadRequestException("Mật khẩu cũ không chính xác")
        if old_password == new_password:
            raise BadRequestException("Mật khẩu mới phải khác mật khẩu cũ")

        current_user.password = hash_password(new_password)
        await self.user_repo.update(current_user)
        await self.refresh_token_repo.revoke_all_for_user(current_user.id)


class UserService:
    def __init__(self, user_repo: UserRepoDep):
        self.user_repo = user_repo

    def get_profile(self, current_user: User):
        return current_user

    async def update_profile(self, current_user: User, update_data: UserUpdate) -> User:
        data = update_data.model_dump(exclude_unset=True, exclude_none=True)
        if "email" in data and data["email"] != current_user.email:
            existing_user = await self.user_repo.get_by_email(data["email"])
            if existing_user:
                raise BadRequestException(
                    "Email này đã được sử dụng bởi tài khoản khác."
                )

        if "username" in data and data["username"] != current_user.username:
            existing_user = await self.user_repo.get_by_username(data["username"])
            if existing_user:
                raise BadRequestException("Username này đã được sử dụng.")
        for field, value in data.items():
            setattr(current_user, field, value)
        updated_user = await self.user_repo.update(current_user)

        return updated_user


class AppointmentService:
    def __init__(
        self,
        appointment_repo: AppointmentRepoDep,
        slot_repo: ScheduleSlotRepoDep,
        doctor_repo: DoctorRepoDep,
        patient_repo: PatientRepoDep,
        medical_record_repo: MedicalRecordRepoDep,
        examination_repo: ExaminationRepoDep,
        prescription_repo: PrescriptionRepoDep,
        prescription_detail_repo: PrescriptionDetailRepoDep,
        medicine_repo: MedicineRepoDep,
        payment_repo: PaymentRepoDep,
    ):
        self.appointment_repo = appointment_repo
        self.slot_repo = slot_repo
        self.doctor_repo = doctor_repo
        self.patient_repo = patient_repo
        self.medical_record_repo = medical_record_repo
        self.examination_repo = examination_repo
        self.prescription_repo = prescription_repo
        self.prescription_detail_repo = prescription_detail_repo
        self.medicine_repo = medicine_repo
        self.payment_repo = payment_repo

    async def get_accessible_appointment(
        self, appointment_id: int, current_user: User
    ) -> Appointment:
        appointment = await self.appointment_repo.get_by_id_with_relations(
            appointment_id
        )
        if not appointment:
            raise ResourceNotFound("Không tìm thấy lịch hẹn")

        if current_user.role == UserRole.ADMIN:
            return appointment

        if current_user.role == UserRole.PATIENT:
            patient = await self.patient_repo.get_by_user_id(current_user.id)
            if not patient or patient.id != appointment.patient_id:
                raise ForbiddenException("Bạn không phải bệnh nhân của lịch hẹn này")
            return appointment

        if current_user.role == UserRole.DOCTOR:
            doctor = await self.doctor_repo.get_by_user_id(current_user.id)
            if not doctor or doctor.id != appointment.slot.schedule.doctor_id:
                raise ForbiddenException("Bạn không phải bác sĩ được phân công")
            return appointment

        raise ForbiddenException(
            "Chỉ bệnh nhân, bác sĩ hoặc quản trị viên mới được xem lịch hẹn này"
        )

    async def get_user_appointments(self, current_user: User) -> list[Appointment]:
        if current_user.role == UserRole.PATIENT:
            return await self.appointment_repo.get_by_patient(current_user.id)
        return await self.appointment_repo.get_by_doctor(current_user.id)

    async def create_appointment(
        self,
        patient: Patient,
        appointment_data: AppointmentCreate,
    ) -> Appointment:
        slot = await self.slot_repo.get_by_id(appointment_data.slot_id)
        if slot is None:
            raise ResourceNotFound("Không tìm thấy khung giờ")

        if slot.status != ScheduleSlotStatus.AVAILABLE:
            raise BadRequestException("Khung giờ không khả dụng")

        existing = await self.appointment_repo.get_by_slot_id(appointment_data.slot_id)
        if existing is not None:
            raise ConflictException("Khung giờ đã được đặt")

        appointment = Appointment(
            patient_id=patient.id,
            slot_id=slot.id,
            status=AppointmentStatus.PENDING,
            reason=appointment_data.reason,
            note=appointment_data.note,
        )
        appointment = await self.appointment_repo.create_with_slot(appointment)
        return appointment

    async def cancel_appointment(
        self,
        appointment_id: int,
        current_user: User,
        cancel_data: AppointmentCancel,
    ):
        appointment = await self.appointment_repo.get_by_id_with_slot(
            appointment_id
        )
        if not appointment:
            raise ResourceNotFound("Không tìm thấy lịch hẹn")

        if current_user.role != UserRole.ADMIN:
            if current_user.role != UserRole.PATIENT:
                raise ForbiddenException("Bạn không có quyền hủy lịch hẹn này")
            patient = await self.patient_repo.get_by_user_id(current_user.id)
            if not patient or appointment.patient_id != patient.id:
                raise ForbiddenException("Bạn không có quyền hủy lịch hẹn này")

        if appointment.status == AppointmentStatus.CANCELLED:
            raise BadRequestException("Lịch hẹn đã được hủy trước đó")
        if appointment.status == AppointmentStatus.COMPLETED:
            raise BadRequestException("Không thể hủy lịch hẹn đã hoàn thành")

        return await self.appointment_repo.cancel(
            appointment, cancel_data.cancel_reason
        )

    async def update_appointment_status(
        self,
        appointment_id: int,
        new_status: AppointmentStatus,
        doctor: Doctor,
    ) -> Appointment:
        appointment = await self.appointment_repo.get_by_id_with_slot(
            appointment_id
        )
        if not appointment:
            raise ResourceNotFound("Không tìm thấy lịch hẹn")

        if appointment.slot.schedule.doctor_id != doctor.id:
            raise ForbiddenException(
                "Bạn không phải bác sĩ được phân công cho lịch hẹn này"
            )

        current_status = appointment.status
        if current_status in (
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.PAID,
        ):
            raise BadRequestException("Không thể thay đổi trạng thái")

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
            raise BadRequestException("Chuyển trạng thái không hợp lệ")

        await self.appointment_repo.update_status(appointment, new_status)
        updated = await self.appointment_repo.get_by_id_with_relations(
            appointment_id
        )
        if not updated:
            raise ResourceNotFound("Không tìm thấy lịch hẹn sau khi cập nhật")
        return updated

    async def get_available_slots(
        self, doctor_id: int, date: date
    ) -> list[ScheduleSlot]:
        return await self.slot_repo.get_available_slots_by_doctor_and_date(
            doctor_id, date
        )

    async def add_examination_record(
        self,
        appointment_id: int,
        doctor: Doctor,
        data: ExaminationRecordCreate,
    ) -> Examination:
        appointment = await self.appointment_repo.get_by_id_with_slot(
            appointment_id
        )
        if not appointment:
            raise ResourceNotFound("Không tìm thấy lịch hẹn")
        if appointment.slot.schedule.doctor_id != doctor.id:
            raise ForbiddenException("Bạn không phải bác sĩ được phân công")
        if appointment.status not in (
            AppointmentStatus.CHECKING_IN,
            AppointmentStatus.EXAMINING,
            AppointmentStatus.COMPLETED,
        ):
            raise BadRequestException("Không thể thêm hồ sơ cho trạng thái này")

        patient = appointment.patient
        if not patient:
            raise ResourceNotFound("Không tìm thấy bệnh nhân")

        medical_record = await self.medical_record_repo.get_by_patient_id(
            patient.id
        )
        if not medical_record:
            medical_record = await self.medical_record_repo.create(
                MedicalRecord(
                    patient_id=patient.id, record_number=generate_record_number()
                )
            )

        status = (
            "completed"
            if appointment.status == AppointmentStatus.COMPLETED
            else "in_progress"
        )

        examination = await self.examination_repo.get_by_appointment(appointment_id)
        if not examination:
            examination = await self.examination_repo.create(
                Examination(
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
                    status=status,
                )
            )
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
            examination = await self.examination_repo.update(examination)

        if data.prescriptions:
            existing_prescriptions = await self.prescription_repo.get_by_examination(
                examination.id
            )
            await self.prescription_repo.delete_many(existing_prescriptions)

            for pres_data in data.prescriptions:
                prescription = await self.prescription_repo.create(
                    Prescription(
                        examination_id=examination.id,
                        prescription_type=pres_data.prescription_type,
                        note=pres_data.note,
                        total_amount=Decimal(0),
                        status=0,
                    )
                )

                total = Decimal(0)
                details = []
                for item in pres_data.items:
                    medicine = await self.medicine_repo.get_by_id(item.medicine_id)
                    if not medicine:
                        raise ResourceNotFound("Không tìm thấy thuốc")
                    unit_price = medicine.current_price
                    subtotal = unit_price * item.quantity
                    total += subtotal
                    details.append(
                        PrescriptionDetail(
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
                    )

                await self.prescription_detail_repo.bulk_create(details)
                prescription.total_amount = total
                await self.prescription_repo.update(prescription)

            await self._safe_refresh(self.examination_repo, examination)
        if appointment.status != AppointmentStatus.COMPLETED:
            await self.appointment_repo.update_status(appointment, AppointmentStatus.COMPLETED)

        full_examination = await self.examination_repo.get_by_appointment(appointment_id)
        return full_examination if full_examination else examination

    @staticmethod
    async def _safe_refresh(repo, obj):
        try:
            await repo.refresh(obj)
        except Exception:
            logger.exception("Failed to refresh object of type %s", type(obj).__name__)

    async def get_appointment_record(
        self, appointment: Appointment
    ) -> Examination:
        examination = await self.examination_repo.get_by_appointment(appointment.id)
        if not examination:
            raise ResourceNotFound("Không tìm thấy hồ sơ khám cho lịch hẹn này")
        return examination

    async def create_payment(
        self,
        appointment_id: int,
        current_user: User,
        payment_method: str | None = None,
    ) -> Payment:
        appointment = await self.appointment_repo.get_by_id_with_relations(
            appointment_id
        )
        if not appointment:
            raise ResourceNotFound("Không tìm thấy lịch hẹn")

        if current_user.role != UserRole.PATIENT:
            raise ForbiddenException("Chỉ bệnh nhân mới có thể tạo thanh toán")
        patient = await self.patient_repo.get_by_user_id(current_user.id)
        if not patient or patient.id != appointment.patient_id:
            raise ForbiddenException("Bạn không phải chủ sở hữu của lịch hẹn này")

        if appointment.status not in (
            AppointmentStatus.COMPLETED,
            AppointmentStatus.PENDING,
        ):
            raise BadRequestException(
                "Chỉ có thể tạo thanh toán cho lịch hẹn đã hoàn thành hoặc đang chờ"
                " xác nhận"
            )

        existing_payment = await self.payment_repo.get_by_appointment(
            appointment_id
        )
        if existing_payment:
            raise ConflictException("Lịch hẹn này đã có thanh toán")

        doctor = appointment.slot.schedule.doctor
        if not doctor:
            raise ResourceNotFound("Không tìm thấy bác sĩ của lịch hẹn này")
        amount = doctor.consultation_fee

        payment = Payment(
            appointment_id=appointment_id,
            amount=amount,
            status=PaymentStatus.PENDING,
            payment_method=payment_method,
            transaction_id=None,
        )
        await self.payment_repo.create(payment)
        await self._safe_refresh(self.payment_repo, payment)

        appointment.status = AppointmentStatus.PAID
        await self.appointment_repo.update(appointment)

        return payment

    async def get_doctor_availability(self, doctor_id: int, work_date: date) -> dict:
        doctor = await self.doctor_repo.get_active_by_id(doctor_id)
        if not doctor:
            raise ResourceNotFound("Không tìm thấy bác sĩ")

        available_slots = await self.slot_repo.get_available_slots_by_doctor_and_date(
            doctor_id, work_date
        )

        if not available_slots:
            return {
                "doctor_id": doctor_id,
                "doctor_name": doctor.user.full_name,
                "specialty": doctor.specialty.name,
                "work_date": work_date,
                "available_slots": []
            }

        return {
            "doctor_id": doctor_id,
            "doctor_name": doctor.user.full_name,
            "specialty": doctor.specialty.name,
            "work_date": work_date,
            "available_slots": [
                ScheduleSlotOut.model_validate(slot) for slot in available_slots
            ]
        }


class SpecialtyService:
    def __init__(
        self,
        specialty_repo: SpecialtyRepoDep,
        doctor_repo: DoctorRepoDep,
    ) -> None:
        self.specialty_repo = specialty_repo
        self.doctor_repo = doctor_repo

    async def get_specialties(self) -> list[Specialty]:
        return await self.specialty_repo.get_active_specialties()

    async def get_specialty(self, specialty_id: int) -> Specialty:
        specialty = await self.specialty_repo.get_active_by_id(specialty_id)
        if specialty is None:
            raise ResourceNotFound("Không tìm thấy chuyên khoa")
        return specialty

    async def create_specialty(
        self, specialty_data: SpecialtyCreate
    ) -> Specialty:
        existed = await self.specialty_repo.get_by_name(specialty_data.name)
        if existed:
            raise ConflictException("Chuyên khoa đã tồn tại")
        specialty = Specialty(**specialty_data.model_dump())
        return await self.specialty_repo.create(specialty)

    async def toggle_specialty_status(self, specialty_id: int) -> Specialty:
        specialty = await self.specialty_repo.get_by_id(specialty_id)
        if specialty is None:
            raise ResourceNotFound("Không tìm thấy chuyên khoa")
        return await self.specialty_repo.toggle_status(specialty)

    async def update_specialty(
        self, specialty_id: int, specialty_data: SpecialtyUpdate
    ) -> Specialty:
        specialty = await self.specialty_repo.get_active_by_id(specialty_id)
        if specialty is None:
            raise ResourceNotFound("Không tìm thấy chuyên khoa")
        if specialty_data.name and specialty_data.name != specialty.name:
            existed = await self.specialty_repo.get_by_name(specialty_data.name)
            if existed:
                raise ConflictException("Chuyên khoa đã tồn tại")

        update_data = specialty_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(specialty, field, value)
        return await self.specialty_repo.update(specialty)


class DoctorService:
    def __init__(
        self,
        doctor_repo: DoctorRepoDep,
        user_repo: UserRepoDep,
        specialty_repo: SpecialtyRepoDep,
        schedule_repo: ScheduleRepoDep,
        appointment_repo: AppointmentRepoDep,
        slot_repo: ScheduleSlotRepoDep,
        examination_repo: ExaminationRepoDep,
    ) -> None:
        self.doctor_repo = doctor_repo
        self.user_repo = user_repo
        self.specialty_repo = specialty_repo
        self.schedule_repo = schedule_repo
        self.appointment_repo = appointment_repo
        self.slot_repo = slot_repo
        self.examination_repo = examination_repo

    async def get_my_patients(self, doctor: Doctor) -> list["PatientSummaryOut"]:
        patients_data = await self.examination_repo.get_patients_by_doctor_id(doctor.id)
        return [PatientSummaryOut.model_validate(p) for p in patients_data]

    async def get_profile_by_user_id(self, user_id: int) -> Doctor:
        doctor = await self.doctor_repo.get_by_user_id(user_id)
        if doctor is None:
            raise ResourceNotFound("Không tìm thấy hồ sơ bác sĩ")
        return doctor

    async def get_doctors(self, specialty_id: int | None = None) -> list[Doctor]:
        if specialty_id is None:
            return await self.doctor_repo.get_active_doctors()
        return await self.doctor_repo.get_by_specialty(specialty_id)

    async def get_doctor(self, doctor_id: int) -> Doctor:
        doctor = await self.doctor_repo.get_active_by_id(doctor_id)
        if doctor is None:
            raise ResourceNotFound("Không tìm thấy bác sĩ")
        return doctor

    async def get_doctor_schedule(self, doctor_id: int):
        doctor = await self.doctor_repo.get_active_by_id(doctor_id)
        if doctor is None:
            raise ResourceNotFound("Không tìm thấy bác sĩ")
        return await self.schedule_repo.get_doctor_available_schedule(doctor_id)

    async def update_my_schedule_slot(
        self,
        slot: ScheduleSlot,
        slot_data: ScheduleSlotUpdate,
    ):
        if slot.status == ScheduleSlotStatus.BOOKED:
            raise BadRequestException("Khung giờ đã đặt không thể sửa")
        update_data = slot_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(slot, field, value)
        return await self.slot_repo.update(slot)

    async def create_doctor(self, doctor_data: DoctorCreate):
        user = await self.user_repo.get_by_id(doctor_data.user_id)
        if user is None:
            raise ResourceNotFound("Không tìm thấy người dùng")
        if user.role != UserRole.DOCTOR:
            raise BadRequestException("Người dùng không phải bác sĩ")
        if await self.doctor_repo.get_by_user_id(doctor_data.user_id):
            raise ConflictException("Hồ sơ bác sĩ đã tồn tại")
        specialty = await self.specialty_repo.get_active_by_id(doctor_data.specialty_id)
        if specialty is None:
            raise ResourceNotFound("Không tìm thấy chuyên khoa")
        if await self.doctor_repo.get_by_license(doctor_data.license_number):
            raise ConflictException("Giấy phép đã tồn tại")
        doctor = Doctor(
            id=doctor_data.user_id, **doctor_data.model_dump(exclude={"user_id"})
        )
        return await self.doctor_repo.create(doctor)

    async def get_my_schedule(self, user: User) -> list["ScheduleOut"]:
        try:
            schedules = await self.schedule_repo.get_schedules_by_doctor_id(user.id)
            return schedules
        except Exception as e:
            return []


class PatientService:
    def __init__(
        self,
        patient_repo: PatientRepoDep,
        medical_record_repo: MedicalRecordRepoDep,
        examination_repo: ExaminationRepoDep,
        doctor_repo: DoctorRepoDep,
        appointment_repo: AppointmentRepoDep,
    ):
        self.patient_repo = patient_repo
        self.medical_record_repo = medical_record_repo
        self.examination_repo = examination_repo
        self.doctor_repo = doctor_repo
        self.appointment_repo = appointment_repo

    async def update_patient_profile(
            self, patient: Patient, update_data: PatientUpdate
    ) -> Patient:
        data = update_data.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(patient, field, value)
        updated_patient = await self.patient_repo.update(patient)
        await self.patient_repo.commit()
        return updated_patient

    async def get_owned_medical_record(self, patient_id: int) -> MedicalRecord:
        record = await self.medical_record_repo.get_by_patient_id(patient_id)
        if record is None:
            raise ResourceNotFound("Không tìm thấy hồ sơ bệnh án")
        return record

    async def get_profile_by_user_id(self, user_id: int) -> Patient:
        patient = await self.patient_repo.get_by_user_id(user_id)
        if patient is None:
            raise ResourceNotFound("Không tìm thấy hồ sơ bệnh nhân")
        return patient

    async def get_patient_medical_history(self, patient_id: int) -> dict:
        medical_record = await self.medical_record_repo.get_by_patient_id(patient_id)
        examinations = await self.examination_repo.get_by_patient(patient_id)
        return {
            "medical_record": medical_record,
            "examinations": examinations,
        }

    async def get_patient_medical_history_with_access(
        self, patient_id: int, current_user: User
    ) -> dict:
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise ResourceNotFound("Không tìm thấy bệnh nhân")
        is_owner = patient.id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN
        is_doctor = current_user.role == UserRole.DOCTOR
        if not (is_owner or is_admin or is_doctor):
            raise ForbiddenException("Bạn không có quyền xem hồ sơ bệnh án này")
        if is_doctor:
            doctor = await self.doctor_repo.get_by_user_id(current_user.id)
            if not doctor:
                raise ResourceNotFound("Không tìm thấy hồ sơ bác sĩ")
            has_access = await self.appointment_repo.exists_by_doctor_and_patient(
                doctor.id, patient_id
            )
            if not has_access:
                raise ForbiddenException(
                    "Bạn không có quyền xem hồ sơ bệnh án của bệnh nhân này"
                )
        medical_record = await self.medical_record_repo.get_by_patient_id(patient_id)
        examinations = await self.examination_repo.get_by_patient(patient_id)
        return {
            "medical_record": medical_record,
            "examinations": examinations
        }


class ScheduleService:
    def __init__(
        self,
        schedule_repo: ScheduleRepoDep,
        slot_repo: ScheduleSlotRepoDep,
    ):
        self.schedule_repo = schedule_repo
        self.slot_repo = slot_repo

    async def get_owned_slot(self, slot_id: int, doctor_id: int) -> ScheduleSlot:
        slot = await self.slot_repo.get_by_id_with_schedule(slot_id)
        if slot is None:
            raise ResourceNotFound("Không tìm thấy khung giờ")
        if slot.schedule.doctor_id != doctor_id:
            raise ForbiddenException(
                "Bạn không thể truy cập khung giờ của bác sĩ khác"
            )
        return slot


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepoDep,
    ):
        self.payment_repo = payment_repo

    async def get_user_payments(self, current_user: User) -> list[PaymentOut]:
        if current_user.role != UserRole.PATIENT:
            raise ForbiddenException("Chỉ bệnh nhân mới được xem lịch sử thanh toán")
        payments = await self.payment_repo.get_by_patient_id(current_user.id)
        return [PaymentOut.model_validate(p) for p in payments]

    async def get_payment_detail(
        self, payment_id: int, current_user: User
    ) -> PaymentOut:
        payment = await self.payment_repo.get_by_id_with_appointment(payment_id)
        if not payment:
            raise ResourceNotFound("Không tìm thấy giao dịch")
        if current_user.role == UserRole.ADMIN:
            return PaymentOut.model_validate(payment)

        if current_user.role == UserRole.PATIENT:
            if payment.appointment.patient_id != current_user.id:
                raise ForbiddenException("Bạn không có quyền xem giao dịch này")
            return PaymentOut.model_validate(payment)

        raise ForbiddenException("Bạn không có quyền truy cập giao dịch này")

class MedicineService:
    def __init__(
        self,
        medicine_repo: MedicineRepoDep,
    ) -> None:
        self.medicine_repo = medicine_repo

    async def get_active_medicines(self, skip: int = 0, limit: int = 100) -> list[Medicine]:
        medicines = await self.medicine_repo.get_active_medicines(skip=skip, limit=limit)
        return medicines


class ReportService:
    def __init__(self, payment_repo: PaymentRepoDep, report_repo: ReportRepoDep):
        self.payment_repo = payment_repo
        self.report_repo = report_repo

    async def get_revenue_report(
        self,
        start_date: datetime,
        end_date: datetime,
        doctor_id: int | None,
        current_user: User,
    ) -> RevenueResponse:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Chỉ ADMIN mới được xem")

        payments = await self.payment_repo.get_revenue_payments(
            start_date, end_date, doctor_id
        )

        total_revenue = Decimal(0)
        items = []
        for payment in payments:
            total_revenue += payment.amount
            doctor_user = payment.appointment.slot.schedule.doctor.user
            patient_user = payment.appointment.patient.user
            items.append(
                RevenueItem(
                    payment_id=payment.id,
                    amount=payment.amount,
                    status=payment.status,
                    payment_method=payment.payment_method,
                    created_date=payment.created_date,
                    doctor_name=doctor_user.full_name,
                    doctor_id=doctor_user.id,
                    patient_name=patient_user.full_name,
                    appointment_id=payment.appointment_id,
                )
            )
        return RevenueResponse(
            total_revenue=total_revenue,
            total_transactions=len(items),
            items=items,
        )

    async def get_patients_by_specialty(
        self,
        start_date: datetime | None,
        end_date: datetime | None,
        current_user: User,
    ) -> PatientsBySpecialtyResponse:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Chỉ ADMIN mới được xem")

        results = await self.report_repo.get_patient_count_by_specialty(
            start_date, end_date
        )
        items = []
        for specialty_id, specialty_name, count in results:
            items.append(
                PatientsBySpecialtyItem(
                    specialty_id=specialty_id,
                    specialty_name=specialty_name,
                    patient_count=count,
                )
            )

        return PatientsBySpecialtyResponse(items=items)

    async def get_appointments_summary(
        self,
        start_date: datetime | None,
        end_date: datetime | None,
        current_user: User,
    ) -> AppointmentsSummaryResponse:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Chỉ ADMIN mới được xem")

        data = await self.report_repo.get_appointment_summary(start_date, end_date)

        by_status = [
            AppointmentStatusCount(status=status, count=count)
            for status, count in data["status_counts"]
        ]

        daily_dict = {}
        for day, status, count in data["daily_rows"]:
            if day not in daily_dict:
                daily_dict[day] = {}
            daily_dict[day][status] = count

        daily_summary = []
        for day, status_counts in daily_dict.items():
            total = sum(status_counts.values())
            daily_summary.append(
                DailyAppointmentSummary(date=day, total=total, by_status=status_counts)
            )
        daily_summary.sort(key=lambda x: x.date)

        return AppointmentsSummaryResponse(
            total_appointments=data["total"],
            by_status=by_status,
            daily_summary=daily_summary,
            start_date=start_date.date() if start_date else None,
            end_date=end_date.date() if end_date else None,
        )

RAG_KEYWORDS = [
    "quy trình",
    "thủ tục",
    "giấy tờ",
    "bảo hiểm",
    "bhyt",
    "giờ làm việc",
    "thời gian",
    "địa chỉ",
    "ở đâu",
    "tái khám",
    "khám bệnh",
    "trái tuyến",
    "thứ 7",
    "thứ bảy",
    "chủ nhật",
    "hướng dẫn",
]

EMERGENCY_KEYWORDS = [
    "khó thở",
    "đau ngực",
    "ngừng tim",
    "bất tỉnh",
    "hôn mê",
    "co giật",
    "nôn ra máu",
    "thuốc sâu",
    "ngộ độc",
    "liệt nửa người",
    "đột quỵ",
    "tai biến",
]

DOCTOR_INTENT_KEYWORDS = [
    "bác sĩ",
    "giá",
    "chi phí",
    "bao nhiêu",
    "danh sách",
    "phòng khám",
]

logger = logging.getLogger(__name__)
_pending_bookings: dict[int, dict[str, Any]] = {}
VN_CHARS = r"a-z0-9_àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"


def normalize_vietnamese(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


class SpecialtyDetectionService:
    def __init__(self):
        self.rules = {
            "Huyết Học": ["huyết học", "truyền máu", "thiếu máu", "tiểu cầu", "bạch cầu"],
            "Mắt": ["mắt", "khoa mắt", "khám mắt", "thị lực", "nhìn mờ", "cận thị", "đau mắt", "đỏ mắt"],
            "Tim Mạch": ["tim mạch", "tim", "huyết áp", "mạch vành", "nhồi máu", "tức ngực", "hồi hộp", "loạn nhịp"],
            "Cơ Xương Khớp": ["xương khớp", "khớp", "cột sống", "thoái hóa", "đau lưng", "thắt lưng", "lưng", "gối", "vai gáy", "thoát vị"],
            "Tiêu Hóa": ["tiêu hóa", "dạ dày", "đau bụng", "ợ chua", "trào ngược", "đại tràng", "gan", "mật", "buồn nôn", "tiêu chảy", "thượng vị"],
            "Tai Mũi Họng": ["tai mũi họng", "tai", "mũi", "họng", "viêm xoang", "ù tai", "nghẹt mũi", "khàn tiếng", "khàn giọng", "amidan"],
            "Da Liễu": ["da liễu", "dị ứng", "mề đay", "mẩn ngứa", "vảy nến", "nấm da", "mụn"],
            "Thần Kinh": ["thần kinh", "đau đầu", "đau nửa đầu", "chóng mặt", "mất ngủ", "đột quỵ", "tai biến", "tê bì"],
            "Phụ Sản": ["sản", "phụ khoa", "thai", "sinh", "kinh nguyệt", "buồng trứng", "tử cung"],
            "Hô Hấp": ["phổi", "hô hấp", "ho", "viêm phế quản", "hen suyễn"],
            "Thận - Tiết Niệu": ["thận", "tiết niệu", "tiểu buốt", "tiểu đêm", "sỏi thận"],
        }

    def detect(self, text: str) -> Optional[str]:
        if not text:
            return None
        text_norm = normalize_vietnamese(text).lower()
        text_norm = re.sub(r'[.,!?;:()\[\]{}"\'\\]', " ", text_norm)
        tokens = text_norm.split()

        if any(token in ["nhi", "nhi khoa", "bé", "trẻ em", "trẻ nhỏ", "sơ sinh", "cháu", "con"] for token in tokens):
            return "Nhi Khoa"
        if "con" in tokens and "tôi" in tokens:
            return "Nhi Khoa"

        if any(term in text_norm for term in ["cấp cứu", "a9", "nguy cấp", "nguy kịch"]):
            return "Cấp Cứu A9"
        if any(term in text_norm for term in ["hồi sức", "icu", "thở máy"]):
            return "Hồi Sức Tích Cực"

        for spec, keywords in self.rules.items():
            for kw in keywords:
                if " " in kw:
                    if kw in text_norm:
                        return spec
                else:
                    if kw in tokens:
                        return spec
        return None


class RAGService:
    def __init__(self):
        self.collection = None
        self.embedding_fn = None
        self.chroma_client = None
        self._initialize()

    def _initialize(self):
        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
            self.collection = self.chroma_client.get_collection(
                name=COLLECTION_NAME, embedding_function=self.embedding_fn
            )
        except Exception:
            logger.exception("Failed to initialize RAG service")
            self.collection = None

    def _search_sync(self, query: str, top_k: int = 3) -> str:
        if not self.collection:
            return ""
        try:
            results = self.collection.query(query_texts=[query], n_results=top_k)
            documents = results.get("documents", [[]])[0]
            if not documents:
                return ""
            return "\n---\n".join(documents)
        except Exception:
            logger.exception("RAG search failed for query: %s", query)
            return ""

    async def search(self, query: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._search_sync, query)


class DoctorSearchService:
    def __init__(self, doctor_repo: DoctorRepoDep):
        self.doctor_repo = doctor_repo

    async def search(
        self,
        specialty_name: str | None = None,
        max_fee: float | None = None,
        doctor_name: str | None = None,
    ) -> tuple[list[Doctor], bool]:
        doctors = await self.doctor_repo.search_doctors_with_filters(
            max_fee=max_fee
        )

        if not doctors:
            return [], False

        if doctor_name:
            search_name = self._normalize_text(doctor_name)
            doctors = [
                d
                for d in doctors
                if d.user
                and search_name in self._normalize_text(d.user.full_name or "")
            ]
            if not doctors:
                return [], False

        if specialty_name:
            search_specialty = self._normalize_text(specialty_name)

            filtered = []
            for doctor in doctors:
                if doctor.specialty and doctor.specialty.name:
                    doctor_specialty = self._normalize_text(doctor.specialty.name)

                    if search_specialty in doctor_specialty:
                        filtered.append(doctor)

            doctors = filtered
            if not doctors:
                return [], False

        doctors.sort(key=lambda d: float(getattr(d, "consultation_fee", 0) or 0))

        return doctors[:5], True

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""

        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])

        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()

        return text

class EmergencyService:
    KEYWORDS = EMERGENCY_KEYWORDS

    def check(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        return any(k in text_lower for k in self.KEYWORDS)

    def get_response(self) -> str:
        return (
            "🚨 **CẢNH BÁO KHẨN CẤP Y TẾ:**\n\n"
            "Các triệu chứng như khó thở dữ dội, đau ngực cấp tính cần được can thiệp y tế NGAY LẬP TỨC!\n\n"
            "🏥 **Trung tâm Cấp cứu A9 – Bệnh viện Bạch Mai:**\n"
            "- **Địa chỉ:** 78 Đường Giải Phóng, Phường Phương Mai, Đống Đa, Hà Nội (Toà nhà A9 - Cổng vào có biển chỉ dẫn cấp cứu trực tiếp).\n"
            "- **Thời gian:** Tiếp nhận bệnh nhân 24/7 (tất cả các ngày trong tuần).\n"
            "- **Hotline Cấp cứu:** 024 3869 3731 hoặc liên hệ ngay **115**.\n\n"
            "⚠️ *Gia đình vui lòng đưa người bệnh đến thẳng Trung tâm Cấp cứu A9, không chờ đợi đặt lịch trực tuyến.*"
        )

class LLMService:
    def __init__(self):
        self.llm = None
        self._initialize()

    def _initialize(self):
        try:
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.1,
                stop=["<|im_end|>", "<|endoftext|>", "User:", "Human:"],
            )
        except Exception:
            logger.exception("Failed to initialize LLM service")
            self.llm = None

    async def generate(self, prompt: str) -> str:
        if not self.llm:
            return (
                "Xin chào, tôi là trợ lý ảo Bệnh viện Bạch Mai. "
                "Hiện tại hệ thống AI đang bận xử lý, vui lòng liên hệ hotline 1900 888 866 hoặc đến trực tiếp 78 Giải Phóng, Hà Nội để được hỗ trợ tốt nhất."
            )
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception:
            logger.exception("LLM generate failed")
            return (
                "Xin chào, tôi là trợ lý ảo Bệnh viện Bạch Mai. "
                "Hiện tại hệ thống AI đang bận xử lý, vui lòng liên hệ hotline 1900 888 866 hoặc đến trực tiếp 78 Giải Phóng, Hà Nội để được hỗ trợ tốt nhất."
            )


class AIChatService:
    FALLBACK_SPECIALTY_RULES = {
        "Mắt": ["mắt", "khoa mắt", "khám mắt"],
        "Nhi Khoa": ["nhi", "trẻ em", "bé", "sốt phát ban"],
        "Huyết Học": ["huyết học", "truyền máu"],
        "Hồi Sức Tích Cực": ["hồi sức", "icu"],
        "Tim Mạch": ["tim mạch", "tim"],
        "Tiêu Hóa": ["tiêu hóa", "dạ dày"],
        "Cơ Xương Khớp": ["xương khớp", "khớp", "cột sống"],
    }

    def __init__(
        self,
        specialty_detector: SpecialtyDetectionService,
        doctor_search: DoctorSearchService,
        rag_service: RAGService,
        emergency_service: EmergencyService,
        llm_service: LLMService,
    ):
        self.specialty_detector = specialty_detector
        self.doctor_search = doctor_search
        self.rag_service = rag_service
        self.emergency_service = emergency_service
        self.llm_service = llm_service

    def _resolve_specialty(
            self, user_message: str, chat_history: list[Any] | None
    ) -> Optional[str]:
        specialty = self.specialty_detector.detect(user_message)
        if specialty or not chat_history:
            return specialty
        for turn in reversed(chat_history):
            role = turn.get("role") if isinstance(turn, dict) else getattr(turn, "role", "user")
            if role != "user":
                continue
            content = turn.get("content") if isinstance(turn, dict) else getattr(turn, "content", "")
            inherited = self.specialty_detector.detect(content)
            if inherited:
                return inherited
        for turn in reversed(chat_history):
            role = turn.get("role") if isinstance(turn, dict) else getattr(turn, "role", "user")
            if role != "user":
                continue
            text_lower = turn.get("content") if isinstance(turn, dict) else getattr(turn, "content", "")
            text_lower = text_lower.lower()
            for spec, kws in self.FALLBACK_SPECIALTY_RULES.items():
                if any(kw in text_lower for kw in kws):
                    return spec
        return None

    def _extract_turn_content(self, msg: Any) -> str:
        if isinstance(msg, dict):
            return f"{msg.get('role', 'User')}: {msg.get('content', '')}"
        if isinstance(msg, (list, tuple)) and len(msg) >= 2:
            return f"{msg[0]}: {msg[1]}"
        if hasattr(msg, "content"):
            role = getattr(msg, "role", "User")
            return f"{role}: {msg.content}"
        return str(msg)

    def _extract_max_fee(self, text: str) -> Optional[float]:
        if not text:
            return None
        text_lower = normalize_vietnamese(text).lower()

        match_unit = re.search(
            r"(\d+[\.,]?\d*)\s*(k|nghìn|ngàn|tr|triệu|đ|đồng|vnd|vnđ)", text_lower
        )
        if match_unit:
            val_str = match_unit.group(1).replace(".", "").replace(",", "")
            unit = match_unit.group(2)
            try:
                val = float(val_str)
                if unit in ["k", "nghìn", "ngàn"]:
                    val *= 1000
                elif unit in ["tr", "triệu"]:
                    val *= 1000000
                return val
            except Exception:
                logger.exception("Failed to parse fee from text: %s", text)
                pass

        match_prefix = re.search(r"(dưới|tầm|khoảng|giá|mức)\s+(\d{2,6})", text_lower)
        if match_prefix:
            try:
                val = float(match_prefix.group(2))
                if val < 1000:
                    val *= 1000
                return val
            except Exception:
                logger.exception("Failed to parse fee prefix from text: %s", text)
                pass
        return None

    def _extract_doctor_name(self, text: str) -> Optional[str]:
        if not text:
            return None
        text_norm = normalize_vietnamese(text)

        prefix_pattern = r"(?:bác\s+sĩ|bs\.?|tiến\s+sĩ|thạc\s+sĩ|pgs\.?\s*ts\.?|gs\.?\s*ts\.?|ts\.?|dr\.?)\s+(?:tên\s+|là\s+|có\s+tên\s+)?([A-ZÀ-Ỹ][a-zà-ỹ\s]+)"
        match = re.search(prefix_pattern, text_norm)

        if match:
            raw_name = match.group(1).strip()
            stop_words = (
                r"\b(có|ở|tại|làm việc|khám|không|tư vấn|cho|nào|được|\?|,|\.)\b"
            )
            clean_name = re.split(stop_words, raw_name, flags=re.IGNORECASE)[0].strip()

            words = clean_name.split()
            if not words:
                return None

            first_word = words[0]
            if not first_word[0].isupper():
                return None

            invalid_starts = [
                "cho", "nào", "tư vấn", "hãy", "giúp", "trực",
                "khoa", "bệnh viện", "trung tâm", "đang", "công tác",
                "làm việc", "phụ trách", "chữa", "khám",
            ]
            if first_word.lower() in invalid_starts:
                return None

            if len(words) >= 2 and words[1].lower() in [
                "công tác", "làm việc", "phụ trách"
            ]:
                return None

            if 2 <= len(words) <= 5:
                if not any(k in clean_name.lower()for k in ["bạch mai", "trung tâm", "khoa", "bệnh viện", "phòng"]):
                    return clean_name

        return None

    def _format_doctors_response(self, doctors: list[Doctor]) -> str:
        if not doctors:
            return "Không tìm thấy bác sĩ phù hợp với yêu cầu của bạn."

        lines = ["Danh sách bác sĩ phù hợp tại Bệnh viện Bạch Mai:"]
        for doc in doctors[:5]:
            s_name = doc.specialty.name if doc.specialty else "Đa Khoa"
            name = doc.user.full_name if doc.user else f"Bác sĩ ID {doc.id}"
            degree = doc.degree or "Bác sĩ"
            fee = float(doc.consultation_fee) if doc.consultation_fee else 0.0
            lines.append(
                f"- {degree} {name} | Chuyên khoa: {s_name} | Giá khám: {fee:,.0f} VNĐ"
            )
        return "\n".join(lines)

    def _build_not_found_message(
        self,
        specialty: Optional[str],
        max_fee: Optional[float],
        doctor_name: Optional[str],
    ) -> str:
        if doctor_name:
            reason = f"Không tìm thấy bác sĩ '{doctor_name}' trong hệ thống của Bệnh viện Bạch Mai."
        elif specialty and max_fee:
            reason = f"Hiện không có bác sĩ nào thuộc chuyên khoa '{specialty}' có giá khám dưới {max_fee:,.0f} VNĐ."
        elif specialty:
            reason = f"Không tìm thấy bác sĩ nào thuộc chuyên khoa '{specialty}' trong cơ sở dữ liệu."
        elif max_fee:
            reason = f"Hiện không có bác sĩ nào có giá khám dưới {max_fee:,.0f} VNĐ."
        else:
            reason = "Không tìm thấy bác sĩ phù hợp với yêu cầu của bạn."
        return (
            f"{reason} Bạn nên đến Khoa Khám bệnh (78 Giải Phóng, Hà Nội) "
            f"để đăng ký khám theo diện BHYT hoặc khám thông thường."
        )

    def _build_rag_prompt(
        self, user_message: str, context_rag: str, chat_history: list[Any] | None
    ) -> str:
        history_text = ""
        if chat_history:
            history_text = "\n".join(
                [f"- {self._extract_turn_content(msg)}" for msg in chat_history[-4:]]
            )

        return f"""Bạn là Trợ lý AI Bệnh viện Bạch Mai (78 Giải Phóng, Hà Nội).
BẮT BUỘC 100% TRẢ LỜI BẰNG TIẾNG VIỆT.

Lịch sử hội thoại:
{history_text if history_text else "Chưa có."}

Tài liệu quy trình & kiến thức bệnh viện (RAG):
{context_rag if context_rag else "Không có tài liệu tra cứu bổ sung."}

Hãy trả lời câu hỏi: "{user_message}" một cách ân cần, ngắn gọn và luôn hướng dẫn người bệnh đến Khoa Khám bệnh (78 Giải Phóng, Hà Nội) khi cần thiết:"""

    async def chat(
        self, user_message: str, chat_history: list[Any] | None = None
    ) -> dict:
        msg_lower = user_message.lower()

        if self.emergency_service.check(msg_lower):
            return {
                "reply": self.emergency_service.get_response(),
                "suggestions": [],
            }

        specialty = self._resolve_specialty(user_message, chat_history)
        max_fee = self._extract_max_fee(user_message)
        doctor_name = self._extract_doctor_name(user_message)
        logger.info(f"=== LEGACY RESOLVE === specialty={specialty!r} max_fee={max_fee!r} doctor_name={doctor_name!r}")

        is_rag_query = any(k in msg_lower for k in RAG_KEYWORDS)
        context_rag = (
            await self.rag_service.search(user_message) if is_rag_query else ""
        )

        has_explicit_doctor_intent = any(k in msg_lower for k in DOCTOR_INTENT_KEYWORDS)
        logger.info(f"  has_explicit_doctor_intent={has_explicit_doctor_intent}")

        doctor_query_intent = bool(
            max_fee or doctor_name or (specialty and has_explicit_doctor_intent)
        )

        if is_rag_query and not (max_fee or doctor_name or has_explicit_doctor_intent):
            doctor_query_intent = False

        if doctor_query_intent:
            doctors, found = await self.doctor_search.search(
                specialty_name=specialty,
                max_fee=max_fee,
                doctor_name=doctor_name,
            )

            if found:
                reply = self._format_doctors_response(doctors)
                return {
                    "reply": reply,
                    "suggestions": [
                        "Đặt lịch khám",
                        "Xem chi tiết bác sĩ",
                        "Tìm bác sĩ khác",
                    ],
                }
            else:
                reply = self._build_not_found_message(specialty, max_fee, doctor_name)
                return {
                    "reply": reply,
                    "suggestions": [
                        "Đến Khoa Khám bệnh",
                        "Xem quy trình khám",
                        "Tư vấn chuyên khoa khác",
                    ],
                }

        if specialty and not has_explicit_doctor_intent:
            reply = f"Với triệu chứng bạn mô tả, bạn nên đến {specialty} để được khám và tư vấn.\n"
            reply += "Bạn có thể đến Khoa Khám bệnh (78 Giải Phóng, Hà Nội) để được hướng dẫn chi tiết."
            return {
                "reply": reply,
                "suggestions": [
                    f"Xem bác sĩ {specialty}",
                    f"Xem giá khám {specialty}",
                    "Đặt lịch khám",
                    "Xem quy trình khám bệnh",
                ],
            }

        prompt = self._build_rag_prompt(user_message, context_rag, chat_history)
        reply = await self.llm_service.generate(prompt)
        return {
            "reply": reply,
            "suggestions": [
                "Đặt lịch khám",
                "Xem quy trình khám bệnh",
                "Liên hệ hotline",
            ],
        }


_last_availability: dict[int, dict] = {}


class AgentChatService:
    SYSTEM_PROMPT = """Bạn là trợ lý AI của Bệnh viện Bạch Mai, có quyền gọi các công cụ (tool) sau:

    - search_doctors: tìm bác sĩ theo chuyên khoa / giá khám / tên bác sĩ.
    - check_availability: xem lịch trống của MỘT bác sĩ cụ thể (cần doctor_id đã biết).
    - list_specialties: liệt kê toàn bộ chuyên khoa của bệnh viện.
    - book_appointment: ĐỀ XUẤT đặt một khung giờ khám (chỉ đề xuất, hệ thống sẽ hỏi xác nhận lại).
    - search_hospital_knowledge: tra cứu quy trình, chính sách, thủ tục BHYT, giờ làm việc,
      địa chỉ, hướng dẫn hành chính từ tài liệu bệnh viện.

    QUY TẮC BẮT BUỘC:
    1. Khi người dùng muốn TÌM BÁC SĨ → GỌI search_doctors.
    2. Khi người dùng muốn XEM LỊCH TRỐNG:
       - NẾU đã có doctor_id trong lịch sử hội thoại → GỌI check_availability với doctor_id đó.
       - NẾU CHƯA CÓ doctor_id → GỌI search_doctors TRƯỚC để tìm bác sĩ.
    3. Khi người dùng muốn ĐẶT LỊCH:
       - NẾU đã có slot_id → GỌI book_appointment.
       - NẾU CHƯA CÓ slot_id → GỌI check_availability TRƯỚC.
    4. Khi người dùng hỏi về QUY TRÌNH / CHÍNH SÁCH / THỦ TỤC / BHYT / GIỜ LÀM VIỆC /
       ĐỊA CHỈ / TÁI KHÁM / GIẤY TỜ (không liên quan đến tìm bác sĩ hay đặt lịch cụ thể)
       → LUÔN GỌI search_hospital_knowledge, KHÔNG được tự bịa câu trả lời từ kiến thức
       nền của bạn.
    5. KHÔNG BAO GIỜ tự bịa doctor_id hoặc slot_id.

    QUY TẮC ĐỊNH DẠNG QUAN TRỌNG:
    - Khi liệt kê bác sĩ từ kết quả search_doctors, LUÔN in kèm mã số dạng [#doctor_id]
      ngay trước tên, ví dụ: "1. [#5] BSCK II. Đặng Minh Hải - Tim Mạch - 211,000 VND".
    - Khi người dùng nhắc lại tên bác sĩ ở lượt sau, tìm số [#id] tương ứng trong lịch sử
      hội thoại (không tự đoán số nếu không thấy).
    - Khi trả lời dựa trên kết quả search_hospital_knowledge, chỉ dùng thông tin có trong
      tài liệu trả về; nếu tool báo found=False, nói rõ là chưa có tài liệu, hướng dẫn
      liên hệ hotline hoặc đến Khoa Khám bệnh.

    LƯU Ý:
    - "tim mach" (không dấu) = "Tim Mạch" (có dấu)
    - Doctor ID là số nguyên từ kết quả search_doctors

    QUY TẮC XỬ LÝ KHI TOOL TRẢ VỀ found=False (CỰC KỲ QUAN TRỌNG):
    - TUYỆT ĐỐI KHÔNG được nói các câu như: "Tôi sẽ gọi chức năng...", "Để tôi tìm kiếm thêm...", "Tôi sẽ làm điều đó ngay sau đây", "Hãy chờ tôi".
    - BẮT BUỘC phải trả lời ngay lập tức bằng mẫu câu sau: 
      "Tôi không tìm thấy thông tin về yêu cầu này trong tài liệu hiện có. Vui lòng liên hệ trực tiếp bệnh viện (Hotline: 024 3869 3731) để được hỗ trợ chính xác."
    - Không được cố gắng gọi lại tool hoặc mô tả hành động sắp làm.

    QUY TẮC TRÍCH DẪN TUYỆT ĐỐI (KHI DÙNG TOOL RAG):
    1. Khi sử dụng thông tin từ kết quả của tool `search_hospital_knowledge`, bạn PHẢI giữ nguyên chính tả và thuật ngữ gốc.
    2. TUYỆT ĐỐI KHÔNG được paraphrase, viết lại, hoặc tự ý "sáng tạo" cách diễn đạt các thuật ngữ chuyên môn (ví dụ: không được biến "quy trình kỹ thuật" thành các từ sai chính tả như "quy kỵt thuật").
    3. Nếu thông tin trong tài liệu quá phức tạp, hãy tóm tắt ý chính nhưng vẫn phải dùng đúng danh từ riêng và thuật ngữ gốc.
    4. Nếu không tìm thấy thông tin, hãy nói rõ: "Tôi không tìm thấy thông tin này trong tài liệu", KHÔNG được bịa ra các quy trình hoặc kỹ thuật không có trong context.
    """

    BOOKING_SUCCESS_CLAIM_PATTERNS = [
        "đã đặt lịch thành công",
        "đặt lịch thành công",
        "booking successful",
        "đã xác nhận đặt lịch",
        "lịch hẹn đã được tạo",
    ]

    MAX_TOOL_ROUNDS = 3
    CONFIRM_KEYWORDS = [
        "đồng ý",
        "xác nhận",
        "ok",
        "oke",
        "đặt luôn",
        "chốt",
        "được",
        "vâng",
        "yes",
    ]
    DECLINE_KEYWORDS = ["không", "hủy", "thôi", "để sau", "cancel"]

    def __init__(
        self,
        specialty_detector: SpecialtyDetectionService,
        doctor_search: DoctorSearchService,
        rag_service: RAGService,
        emergency_service: EmergencyService,
        specialty_service: SpecialtyService,
        appointment_service: AppointmentService,
        patient_service: PatientService,
        legacy_chat_service: AIChatService,
    ):
        self.specialty_detector = specialty_detector
        self.doctor_search = doctor_search
        self.rag_service = rag_service
        self.emergency_service = emergency_service
        self.specialty_service = specialty_service
        self.appointment_service = appointment_service
        self.patient_service = patient_service
        self.legacy_chat_service = legacy_chat_service

        self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0,
            stop=["<|im_end|>", "<|endoftext|>", "User:", "Human:"],
        )

    def _normalize_specialty_text(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        text = text.lower().replace("viện", "").replace("trung tâm", "").replace("khoa", "")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    async def chat(
        self,
        session_id: int,
        user_message: str,
        chat_history: list[Any] | None,
        current_user: User,
    ) -> dict:
        logger.info(f"\n{'='*60}\n>>> INCOMING: session={session_id} msg={user_message!r}\n{'='*60}")
        msg_lower = user_message.lower()

        if self.emergency_service.check(msg_lower):
            return {"reply": self.emergency_service.get_response(), "suggestions": []}

        pending = _pending_bookings.get(session_id)
        if pending:
            confirm_result = await self._handle_pending_confirmation(
                session_id, msg_lower, pending, current_user
            )
            if confirm_result is not None:
                return confirm_result
            _pending_bookings.pop(session_id, None)

        patient: Optional[Patient] = None
        try:
            patient = await self.patient_service.get_profile_by_user_id(current_user.id)
        except ResourceNotFound:
            logger.info(
                "User %s chưa có hồ sơ Patient — tắt tool book_appointment",
                current_user.id,
            )

        try:
            result = await self._run_agent(
                session_id, user_message, chat_history, current_user, patient
            )
            if result is not None:
                return result
        except Exception:
            logger.exception(
                "Agent pipeline thất bại, fallback về AIChatService legacy"
            )

        return await self.legacy_chat_service.chat(user_message, chat_history)

    async def _handle_pending_confirmation(
        self,
        session_id: int,
        msg_lower: str,
        pending: dict[str, Any],
        current_user: User,
    ) -> Optional[dict]:
        if any(k in msg_lower for k in self.CONFIRM_KEYWORDS):
            slot_id = pending["slot_id"]
            try:
                patient = await self.patient_service.get_profile_by_user_id(current_user.id)
            except ResourceNotFound:
                _pending_bookings.pop(session_id, None)
                return {
                    "reply": "Tài khoản của bạn chưa có hồ sơ bệnh nhân nên chưa thể đặt lịch. "
                    "Vui lòng hoàn thiện hồ sơ trước khi đặt lịch khám.",
                    "suggestions": ["Hoàn thiện hồ sơ", "Liên hệ hotline"],
                }

            try:
                logger.info("=== EXECUTE TOOL: book_appointment ===")
                logger.info(f"=== TOOL ARGS: slot_id={slot_id}, patient_id={patient.id} ===")

                appointment = await self.appointment_service.create_appointment(
                    patient=patient,
                    appointment_data=AppointmentCreate(slot_id=slot_id),
                )

                logger.info(f"=== BOOKING RESULT: appointment_id={appointment.id}, status={appointment.status} ===")

                _pending_bookings.pop(session_id, None)
                return {
                    "reply": (
                        f"✅ Đã đặt lịch khám thành công (mã lịch hẹn #{appointment.id}). "
                        "Bạn vui lòng đến trước giờ hẹn 15 phút để làm thủ tục."
                    ),
                    "suggestions": ["Xem lịch hẹn của tôi", "Đặt thêm lịch khác"],
                }
            except (ResourceNotFound, BadRequestException, ConflictException) as e:
                _pending_bookings.pop(session_id, None)
                logger.warning("Không thể đặt lịch: %s", e)
                return {
                    "reply": "Rất tiếc, không thể đặt lịch. Bạn muốn chọn khung giờ khác không?",
                    "suggestions": ["Tìm khung giờ khác", "Tìm bác sĩ khác"],
                }

        if any(k in msg_lower for k in self.DECLINE_KEYWORDS):
            _pending_bookings.pop(session_id, None)
            return {
                "reply": "Đã hủy đề xuất đặt lịch. Bạn cần mình hỗ trợ gì thêm không?",
                "suggestions": ["Tìm bác sĩ khác", "Xem chuyên khoa"],
            }

        return {
            "reply": (
                f"Bạn có muốn xác nhận đặt khung giờ đã đề xuất (mã slot #{pending['slot_id']}) không? "
                "Trả lời 'xác nhận' để đặt, hoặc 'hủy' nếu không muốn nữa."
            ),
            "suggestions": ["Xác nhận", "Hủy"],
        }

    def _has_small_doctor_ids(self, content: str) -> bool:
        if not content:
            return False
        matches = re.findall(r'\[#(\d+)\]', content)

        for match in matches:
            doctor_id = int(match)
            if doctor_id < 100:
                logger.warning(f"  🚨 Phát hiện doctor_id nhỏ bất thường: #{doctor_id}")
                return True

        return False

    def _claims_booking_success_without_tool(self, content: str, tool_calls: list) -> bool:
        if tool_calls:
            return False
        if not content:
            return False
        content_lower = content.lower()

        proposal_patterns = [
            "đề xuất",
            "bạn có muốn",
            "bạn xác nhận",
            "bạn đồng ý",
            "có muốn đặt",
            "xác nhận đặt",
        ]

        if any(p in content_lower for p in proposal_patterns):
            logger.info("  → Content là đề xuất, không phải claim success")
            return False

        return any(p in content_lower for p in self.BOOKING_SUCCESS_CLAIM_PATTERNS)

    def _is_in_booking_flow(self, user_message: str) -> bool:
        logger.info(f"=== CHECK _is_in_booking_flow ===")
        logger.info(f"  user_message: {user_message!r}")

        content_lower = user_message.lower()

        confirm_keywords = [
            "xác nhận",
            "đồng ý",
            "đặt luôn",
            "chốt",
            "ok",
            "oke",
            "được",
            "vâng",
            "yes",
        ]
        decline_keywords = [
            "hủy",
            "thôi",
            "để sau",
            "cancel",
            "đổi ý",
        ]
        slot_keywords = [
            "khung giờ đầu tiên",
            "slot",
            "mã slot",
            "khung giờ khám",
            "khung giờ",
        ]

        all_keywords = confirm_keywords + decline_keywords + slot_keywords

        for k in all_keywords:
            if k in content_lower:
                logger.info(f"  → True (khớp keyword {k!r} trong tin nhắn hiện tại)")
                return True

        logger.info("  → False (tin nhắn hiện tại không khớp keyword nào)")
        return False

    def _replace_hallucination(self, content: str) -> str:
        if not content:
            return content

        hallucination_patterns = [
            r"tôi sẽ gọi chức năng",
            r"tôi sẽ gọi tool",
            r"ngay sau đây",
            r"tôi sẽ tìm kiếm thêm",
            r"hãy chờ tôi gọi",
            r"tôi sẽ thực hiện điều này"
        ]

        content_lower = content.lower()
        if any(re.search(p, content_lower) for p in hallucination_patterns):
            logger.warning("⚠️ Phát hiện LLM narrate tool call (ảo giác), đang chặn và sửa lại response.")
            return (
                "Tôi không tìm thấy thông tin cụ thể về yêu cầu này trong tài liệu hiện có. "
                "Vui lòng liên hệ trực tiếp với bệnh viện để được hỗ trợ chính xác nhất."
            )
        return content

    async def _verify_doctor_exists(self, doctor_id: int) -> bool:
        try:
            doctor = await self.doctor_search.doctor_repo.get_by_id(doctor_id)
            return doctor is not None
        except Exception:
            return False

    def _extract_doctor_name_from_history(
        self, chat_history: list[Any] | None
    ) -> str | None:
        if not chat_history:
            return None


        for turn in reversed(chat_history[-5:]):
            content = (
                turn.get("content", "")
                if isinstance(turn, dict)
                else getattr(turn, "content", "")
            )
            matches = re.findall(
                r"(?:bác sĩ|BS|bs)\s+([A-ZÀ-Ỹ][a-zà-ỹ]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]*)+)",
                content,
            )
            if matches:
                return matches[-1]

        return None

    def _parse_doctor_id_from_history(
        self, chat_history: list[Any] | None
    ) -> int | None:
        if not chat_history:
            return None

        for turn in reversed(chat_history[-10:]):
            content = (
                turn.get("content", "")
                if isinstance(turn, dict)
                else getattr(turn, "content", "")
            )
            matches = re.findall(r"\[#(\d{3,})\]", content)
            if matches:
                doctor_id = int(matches[-1])
                logger.info(
                    f"  Parse doctor_id từ history (turn gần nhất): {doctor_id}"
                )
                return doctor_id

        return None

    AVAILABILITY_KEYWORDS = [
        "xem lịch",
        "lịch trống",
        "khung giờ",
        "còn lịch",
        "lịch khám",
    ]
    DATE_PATTERN = r"(\d{1,2})/(\d{1,2})/(\d{4})"

    SEARCH_DOCTOR_PATTERNS = [
        r"tìm bác sĩ",
        r"tim bac si",
        r"bác sĩ chuyên khoa",
        r"khám bác sĩ",
        r"bác sĩ tên",
        r"giá khám",
        r"giá dưới",
        r"đặt lịch khám",
        r"đặt khám",
        r"khám chuyên khoa",
        r"có bác sĩ",
        r"bên .* có bác sĩ",
    ]

    def _extract_availability_intent(
        self, user_message: str, chat_history
    ) -> dict | None:

        msg = user_message.lower()

        date_match = re.search(self.DATE_PATTERN, user_message)
        if not date_match:
            return None

        if not any(kw in msg for kw in self.AVAILABILITY_KEYWORDS):
            return None

        doctor_id = self._parse_doctor_id_from_message(user_message)
        if not doctor_id:
            doctor_id = self._parse_doctor_id_from_history(chat_history)

        if not doctor_id:
            return None

        day, month, year = date_match.groups()
        work_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        logger.info(
            f"  Availability intent detected: doctor_id={doctor_id}, work_date={work_date}"
        )

        return {
            "doctor_id": doctor_id,
            "work_date": work_date,
        }

    def _parse_doctor_id_from_message(self, user_message: str) -> int | None:

        matches = re.findall(r"\[#(\d+)\]", user_message)
        if matches:
            return int(matches[-1])
        return None

    RAG_INTENT_KEYWORDS = [
        "quy trình",
        "thủ tục",
        "giấy tờ",
        "bảo hiểm",
        "bhyt",
        "hoàn tiền",
        "chính sách",
        "giờ làm việc",
        "địa chỉ",
        "tái khám",
        "trái tuyến",
        "hướng dẫn",
    ]

    def _requires_tool_call(self, user_message: str) -> bool:
        msg = user_message.lower()

        if any(re.search(p, msg) for p in self.SEARCH_DOCTOR_PATTERNS):
            return True

        if any(kw in msg for kw in self.AVAILABILITY_KEYWORDS):
            return True

        if "đặt lịch" in msg or "đặt khám" in msg:
            return True

        if any(kw in msg for kw in self.RAG_INTENT_KEYWORDS):
            return True

        return False

    async def _extract_search_intent(self, user_message: str) -> dict | None:
        msg = user_message.lower()
        if not any(re.search(p, msg) for p in self.SEARCH_DOCTOR_PATTERNS):
            return None

        specialty_name = await self._extract_specialty_from_message(user_message)
        doctor_name = self._extract_doctor_name_from_message(user_message)

        if (
            doctor_name
            and specialty_name
            and doctor_name.lower() == specialty_name.lower()
        ):
            logger.info(
                f"  Doctor name '{doctor_name}' trùng specialty — bỏ doctor_name"
            )
            doctor_name = None

        max_fee = self._extract_max_fee_from_message(user_message)

        if not specialty_name and not doctor_name:
            msg_lower = user_message.lower()
            if not re.search(r"giá\s+khám|giá\s+dưới|giá\s+trên", msg_lower):
                specialty_match = re.search(
                    r"(?:khám|đặt lịch khám)\s+(?:chuyên khoa\s+)?([^\d,.!?]+)",
                    msg_lower,
                )
                if specialty_match:
                    candidate = specialty_match.group(1).strip()
                    phrase_stopwords = ["bác sĩ", "bs "]
                    word_stopwords = {
                        "giá",
                        "dưới",
                        "trên",
                        "nghìn",
                        "đồng",
                        "vnd",
                        "tiền",
                        "tên",
                    }
                    candidate_words = set(candidate.split())
                    has_phrase_stopword = any(p in candidate for p in phrase_stopwords)
                    has_word_stopword = bool(
                        candidate_words.intersection(word_stopwords)
                    )
                    if (
                            candidate not in word_stopwords
                            and not has_phrase_stopword
                            and not has_word_stopword
                    ):
                        specialty_name = candidate

        logger.info(f"  Search intent parsed: specialty={specialty_name!r} doctor={doctor_name!r} fee={max_fee!r}")

        return {
            "specialty_name": specialty_name,
            "doctor_name": doctor_name,
            "max_fee": max_fee,
        }

    async def _extract_specialty_from_message(self, user_message: str) -> str | None:
        msg = user_message.strip()

        spec_match = re.search(r"chuyên khoa\s+([^\d,.!?]+)", msg, re.IGNORECASE)
        if spec_match:
            result = spec_match.group(1).strip()
            if result:
                return result

        if re.search(r"tim\s*m[ạa]ch", msg, re.IGNORECASE):
            return "Tim Mạch"

        if self.specialty_service:
            try:
                specialties = await self.specialty_service.get_specialties()
                msg_norm = self._normalize_specialty_text(msg)
                for s in specialties:
                    s_norm = self._normalize_specialty_text(s.name)
                    if s_norm and s_norm in msg_norm:
                        return s.name
            except Exception:
                pass

        return self.specialty_detector.detect(user_message)

    def _extract_doctor_name_from_message(self, user_message: str) -> str | None:
        msg = user_message.strip()

        name_match = re.search(r"tên\s+([^\d,.!?]+)", msg, re.IGNORECASE)
        if name_match:
            result = name_match.group(1).strip()
            if result:
                return result

        patterns = [
            r"(?:bác sĩ|BS)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, msg)
            if match:
                return match.group(1).strip()

        return None

    def _extract_max_fee_from_message(self, user_message: str) -> float | None:
        msg = user_message.lower()

        fee_match = re.search(r"dưới\s+(\d+)\s*(nghìn|ngàn|k)?", msg)
        if fee_match:
            val = int(fee_match.group(1))
            if fee_match.group(2):
                val *= 1000
            return float(val)

        generic_fee = re.search(r"(\d+)\s*(?:nghìn|ngàn|k)", msg)
        if generic_fee:
            return float(int(generic_fee.group(1)) * 1000)

        return None

    async def _find_doctor_id_by_name(self, doctor_name: str) -> int | None:
        try:
            doctors, found = await self.doctor_search.search(doctor_name=doctor_name)
            if found and doctors:
                return doctors[0].id
        except Exception:
            pass
        return None

    def _build_tools(self, has_patient: bool) -> list:
        tools = [
            StructuredTool.from_function(
                func=lambda **kwargs: None,
                name="search_doctors",
                description="Tìm bác sĩ theo chuyên khoa, giá khám tối đa, hoặc tên bác sĩ.",
                args_schema=SearchDoctorsInput,
            ),
            StructuredTool.from_function(
                func=lambda **kwargs: None,
                name="check_availability",
                description="Xem các khung giờ trống của một bác sĩ cụ thể theo ngày.",
                args_schema=CheckAvailabilityInput,
            ),
            StructuredTool.from_function(
                func=lambda **kwargs: None,
                name="list_specialties",
                description="Liệt kê tất cả chuyên khoa hiện có của bệnh viện.",
                args_schema=ListSpecialtiesInput,
            ),
            StructuredTool.from_function(
                func=lambda **kwargs: None,
                name="search_hospital_knowledge",
                description=(
                    "Tra cứu chính sách, quy trình khám bệnh, thủ tục BHYT, tái khám, "
                    "giờ làm việc, địa chỉ, hướng dẫn hành chính từ tài liệu bệnh viện. "
                    "GỌI TOOL NÀY khi câu hỏi KHÔNG phải tìm bác sĩ/xem lịch/đặt lịch mà "
                    "là hỏi về quy trình, chính sách, thủ tục, giờ giấc, giấy tờ."
                ),
                args_schema=SearchKnowledgeInput,
            ),
        ]

        if has_patient:
            tools.append(
                StructuredTool.from_function(
                    func=lambda **kwargs: None,
                    name="book_appointment",
                    description="Đề xuất đặt một khung giờ khám cụ thể (chưa đặt thật, chỉ đề xuất để người dùng xác nhận).",
                    args_schema=BookAppointmentInput,
                )
            )

        return tools

    def _history_to_messages(self, chat_history: list[Any] | None) -> list:
        messages: list = [SystemMessage(content=self.SYSTEM_PROMPT)]

        if chat_history:
            for turn in chat_history[-6:]:
                role = (
                    turn.get("role")
                    if isinstance(turn, dict)
                    else getattr(turn, "role", "user")
                )
                content = (
                    turn.get("content")
                    if isinstance(turn, dict)
                    else getattr(turn, "content", "")
                )
                if role == "assistant":
                    messages.append(AIMessage(content=content))
                else:
                    messages.append(HumanMessage(content=content))
        return messages

    async def _run_agent(
        self, session_id, user_message, chat_history, current_user, patient
    ):
        tools = self._build_tools(has_patient=patient is not None)
        llm_with_tools = self.llm.bind_tools(tools)

        messages = self._history_to_messages(chat_history)
        messages.append(HumanMessage(content=user_message))

        availability_intent = self._extract_availability_intent(user_message, chat_history)
        if availability_intent:
            logger.info(f"=== DETERMINISTIC ROUTING: Availability intent detected: {availability_intent} ===")
            tool_result = await self._execute_read_tool("check_availability", availability_intent, chat_history)

            if tool_result.get("error"):
                return {
                    "reply": tool_result["error"],
                    "suggestions": ["Tìm bác sĩ khác", "Liên hệ hotline"],
                }

            _last_availability[session_id] = {
                "doctor_id": tool_result.get("doctor_id"),
                "work_date": tool_result.get("work_date"),
                "slots": [
                    {"slot_id": s["slot_id"], "start_time": s["start_time"], "end_time": s["end_time"]}
                    for s in tool_result.get("available_slots", [])
                ],
            }
            logger.info(f"  Đã lưu _last_availability: doctor_id={_last_availability[session_id]['doctor_id']}, slots={len(_last_availability[session_id]['slots'])}")

            slots = tool_result.get("available_slots", [])
            doctor_name = tool_result.get("doctor_name", f"Bác sĩ #{tool_result.get('doctor_id')}")
            work_date = tool_result.get("work_date", "")

            if not slots:
                return {
                    "reply": f"{doctor_name} không có lịch trống vào ngày {work_date}. Bạn có thể chọn ngày khác hoặc bác sĩ khác.",
                    "suggestions": ["Tìm bác sĩ khác", "Xem chuyên khoa"],
                }

            formatted_slots = []
            for idx, slot in enumerate(slots, 1):
                formatted_slots.append(
                    f"{idx}. Khung giờ #{slot['slot_id']}: {slot['start_time']} - {slot['end_time']}"
                )
            slots_text = "\n".join(formatted_slots)

            return {
                "reply": f"{doctor_name} có các khung giờ trống ngày {work_date}:\n\n{slots_text}\n\nBạn muốn đặt khung giờ nào?",
                "suggestions": ["Đặt khung giờ đầu tiên", "Chọn bác sĩ khác"],
            }
        search_intent = await self._extract_search_intent(user_message)
        if search_intent:
            logger.info(
                f"=== DETERMINISTIC ROUTING: Search intent detected: {search_intent} ==="
            )
            tool_result = await self._execute_read_tool(
                "search_doctors", search_intent, chat_history
            )

            if tool_result.get("found"):
                return {
                    "reply": tool_result["formatted_text"],
                    "suggestions": ["Xem lịch trống", "Đặt lịch khám"],
                }
            else:
                message = tool_result.get("message", "Không tìm thấy bác sĩ phù hợp.")
                logger.info(f"  Search không tìm thấy: {message}")
                return {
                    "reply": message,
                    "suggestions": ["Tìm bác sĩ khác", "Xem chuyên khoa", "Liên hệ hotline"],
                }
        logger.info("=" * 60)
        logger.info(f"AGENT LOOP BẮT ĐẦU - User: {current_user.username}")
        logger.info(f"Message: {user_message}")
        logger.info(f"Tools available: {[t.name for t in tools]}")
        logger.info("=" * 60)

        for _round in range(self.MAX_TOOL_ROUNDS):
            try:
                ai_response: AIMessage = await asyncio.wait_for(
                    llm_with_tools.ainvoke(messages), timeout=60.0
                )
            except asyncio.TimeoutError:
                logger.error(f"LLM timeout sau 60s ở round {_round + 1}")
                if _round == 0:
                    return await self.legacy_chat_service.chat(
                        user_message, chat_history
                    )
                else:
                    return {
                        "reply": "Xin lỗi, hệ thống đang quá tải. Bạn vui lòng thử lại sau ít phút.",
                        "suggestions": ["Thử lại", "Liên hệ hotline"],
                    }
            tool_calls = getattr(ai_response, "tool_calls", None) or []

            if not tool_calls and self._is_in_booking_flow(user_message):
                logger.info("  → Đang trong booking flow, xử lý deterministic")
                pass
            elif self._claims_booking_success_without_tool(
                    getattr(ai_response, "content", ""), tool_calls
            ):
                logger.error("  🚨 LLM claim đặt lịch thành công nhưng KHÔNG gọi tool — chặn lại")
                return {
                    "reply": "Xin lỗi, tôi chưa thể xác nhận đặt lịch. Vui lòng thử lại yêu cầu đặt lịch.",
                    "suggestions": ["Xem lịch trống", "Tìm bác sĩ"],
                }

            logger.info(f"Round {_round + 1}:")
            logger.info(
                f"  Content: {ai_response.content[:100] if ai_response.content else 'None'}"
            )
            logger.info(f"  Tool calls: {len(tool_calls)}")

            for call in tool_calls:
                logger.info(f"    → {call['name']}({call.get('args', {})})")

            if not tool_calls and _round == 0:
                logger.warning(
                    "  → LLM không gọi tool ở round 0, retry với prompt mạnh hơn"
                )
                retry_messages = messages + [
                    SystemMessage(
                        content="BẮT BUỘC: Bạn phải gọi một tool phù hợp. "
                        "Nếu người dùng muốn tìm bác sĩ, gọi search_doctors. "
                        "Nếu muốn xem lịch, gọi check_availability. "
                        "Nếu muốn đặt lịch, gọi book_appointment. "
                        "KHÔNG trả lời trực tiếp nếu có thể dùng tool."
                    )
                ]
                try:
                    retry_response = await asyncio.wait_for(
                        llm_with_tools.ainvoke(retry_messages), timeout=60.0
                    )
                    retry_tool_calls = getattr(retry_response, "tool_calls", None) or []

                    if retry_tool_calls:
                        logger.info(
                            f"  ✅ Retry thành công: LLM gọi {len(retry_tool_calls)} tool"
                        )
                        ai_response = retry_response
                        tool_calls = retry_tool_calls
                        messages = retry_messages
                    else:
                        logger.warning("  ❌ Retry vẫn không gọi tool")
                except asyncio.TimeoutError:
                    logger.error("  ❌ Retry timeout")

            if not tool_calls:
                if _round == 0:
                    if self._is_in_booking_flow(user_message):
                        logger.warning("  → Đang giữa flow đặt lịch, xử lý trực tiếp")

                        msg_lower = user_message.lower()

                        if any(
                            k in msg_lower for k in ["hủy", "thôi", "cancel", "đổi ý"]
                        ):
                            _pending_bookings.pop(session_id, None)
                            return {
                                "reply": "Đã hủy đề xuất đặt lịch. Bạn cần mình hỗ trợ gì thêm không?",
                                "suggestions": ["Tìm bác sĩ khác", "Xem chuyên khoa"],
                            }

                        if any(
                            k in msg_lower
                            for k in [
                                "xác nhận",
                                "đồng ý",
                                "đặt luôn",
                                "chốt",
                                "ok",
                                "oke",
                                "được",
                                "vâng",
                                "yes",
                            ]
                        ):
                            pending = _pending_bookings.get(session_id)
                            if pending:
                                confirm_result = (
                                    await self._handle_pending_confirmation(
                                        session_id, msg_lower, pending, current_user
                                    )
                                )
                                if confirm_result is not None:
                                    return confirm_result
                                _pending_bookings.pop(session_id, None)
                            else:
                                return {
                                    "reply": "Bạn muốn xác nhận đặt lịch nào? Hiện tại chưa có đề xuất nào đang chờ.",
                                    "suggestions": [
                                        "Tìm bác sĩ",
                                        "Xem lịch trống",
                                        "Đặt lịch khám",
                                    ],
                                }
                        if any(k in msg_lower for k in ["khung giờ", "slot"]):
                            slot_id_match = re.search(r"#(\d+)", user_message)
                            if slot_id_match:
                                requested_slot_id = int(slot_id_match.group(1))
                                logger.info(
                                    f"  User chỉ định slot_id={requested_slot_id}"
                                )
                            else:
                                requested_slot_id = None

                            if requested_slot_id:
                                logger.info(
                                    f"  Tra DB trực tiếp slot_id={requested_slot_id}..."
                                )
                                slot_info = await self.appointment_service.appointment_repo.get_slot_with_doctor(
                                    requested_slot_id
                                )

                                if not slot_info:
                                    return {
                                        "reply": f"Khung giờ #{requested_slot_id} không tồn tại. Bạn vui lòng chọn khung giờ khác.",
                                        "suggestions": [
                                            "Xem lịch trống",
                                            "Tìm bác sĩ khác",
                                        ],
                                    }

                                if slot_info["status"] != ScheduleSlotStatus.AVAILABLE:
                                    return {
                                        "reply": f"Khung giờ #{requested_slot_id} không còn trống. Bạn vui lòng chọn khung giờ khác.",
                                        "suggestions": [
                                            "Xem lịch trống",
                                            "Chọn khung giờ khác",
                                        ],
                                    }

                                doctor_id = slot_info["doctor_id"]
                                start_time = slot_info["start_time"]

                                _pending_bookings[session_id] = {
                                    "slot_id": requested_slot_id,
                                    "reason": None,
                                }

                                logger.info(
                                    f"  ✅ Tìm thấy slot #{requested_slot_id}: doctor_id={doctor_id}, start_time={start_time}"
                                )
                                return {
                                    "reply": f"Bạn muốn đặt khung giờ {start_time} (mã slot #{requested_slot_id}) "
                                    f"với bác sĩ [#{doctor_id}]? Vui lòng xác nhận để hoàn tất đặt lịch.",
                                    "suggestions": ["Xác nhận đặt lịch", "Hủy bỏ"],
                                }

                            last_ctx = _last_availability.get(session_id)
                            if last_ctx:
                                logger.info(
                                    f"  Sử dụng _last_availability: doctor_id={last_ctx['doctor_id']}, work_date={last_ctx['work_date']}"
                                )
                                doctor_id = last_ctx["doctor_id"]
                                work_date = last_ctx["work_date"]
                                slots = last_ctx.get("slots", [])
                            else:
                                doctor_id = self._parse_doctor_id_from_message(
                                    user_message
                                )
                                if not doctor_id:
                                    doctor_id = self._parse_doctor_id_from_history(
                                        chat_history
                                    )
                                work_date = "2026-09-15"
                                slots = []

                            if not doctor_id:
                                return {
                                    "reply": "Bạn vui lòng chọn bác sĩ trước, sau đó mình sẽ xem lịch trống và đề xuất khung giờ phù hợp.",
                                    "suggestions": [
                                        "Tìm bác sĩ",
                                        "Xem chuyên khoa",
                                    ],
                                }

                            if slots:
                                selected_slot = slots[0]
                                slot_id = selected_slot["slot_id"]
                                start_time = selected_slot["start_time"]

                                _pending_bookings[session_id] = {
                                    "slot_id": slot_id,
                                    "reason": None,
                                }

                                return {
                                    "reply": f"Bạn muốn đặt khung giờ {start_time} (mã slot #{slot_id}) với bác sĩ [#{doctor_id}]? "
                                    f"Vui lòng xác nhận để hoàn tất đặt lịch.",
                                    "suggestions": ["Xác nhận đặt lịch", "Hủy bỏ"],
                                }

                            try:
                                availability_result = await self._execute_read_tool(
                                    "check_availability",
                                    {"doctor_id": doctor_id, "work_date": work_date},
                                    chat_history,
                                )

                                slots = availability_result.get("available_slots", [])
                                if not slots:
                                    return {
                                        "reply": f"Bác sĩ [#{doctor_id}] không có khung giờ trống. Bạn muốn chọn ngày khác hoặc bác sĩ khác không?",
                                        "suggestions": ["Tìm bác sĩ khác", "Xem chuyên khoa"],
                                    }

                                _last_availability[session_id] = {
                                    "doctor_id": doctor_id,
                                    "work_date": work_date,
                                    "slots": [
                                        {"slot_id": s["slot_id"], "start_time": s["start_time"], "end_time": s["end_time"]}
                                        for s in slots
                                    ],
                                }

                                selected_slot = slots[0]
                                slot_id = selected_slot["slot_id"]
                                start_time = selected_slot["start_time"]

                                _pending_bookings[session_id] = {
                                    "slot_id": slot_id,
                                    "reason": None,
                                }

                                return {
                                    "reply": f"Bạn muốn đặt khung giờ {start_time} (mã slot #{slot_id}) với bác sĩ [#{doctor_id}]? "
                                    f"Vui lòng xác nhận để hoàn tất đặt lịch.",
                                    "suggestions": ["Xác nhận đặt lịch", "Hủy bỏ"],
                                }
                            except Exception as e:
                                logger.exception("Lỗi khi gọi check_availability trong booking flow")
                                return {
                                    "reply": "Có lỗi khi kiểm tra lịch trống. Bạn vui lòng thử lại sau.",
                                    "suggestions": ["Tìm bác sĩ khác", "Liên hệ hotline"],
                                }

                    if ai_response.content and len(ai_response.content.strip()) > 10:
                        content = self._replace_hallucination(ai_response.content)
                        content_with_small_ids = self._has_small_doctor_ids(ai_response.content)
                        if content_with_small_ids:
                            logger.warning(f"  → Content chứa doctor_id nhỏ bất thường, có thể hallucinate — fallback legacy")
                            return await self.legacy_chat_service.chat(user_message, chat_history)

                        if self._requires_tool_call(user_message):
                            logger.error(f"  🚨 Intent cần tool nhưng LLM không gọi — từ chối thay vì dùng content bịa")
                            return {
                                "reply": "Xin lỗi, tôi chưa lấy được thông tin chính xác. Bạn vui lòng thử lại.",
                                "suggestions": ["Thử lại", "Liên hệ hotline"],
                            }

                        logger.info("  → LLM không gọi tool nhưng có content hợp lệ, dùng trực tiếp")
                        return {
                            "reply": ai_response.content,
                            "suggestions": ["Tìm bác sĩ khác", "Xem chuyên khoa", "Đặt lịch khám"],
                        }
                else:
                    logger.info("  → LLM tổng hợp kết quả (không cần thêm tool)")
                    final_content = self._replace_hallucination(
                        ai_response.content or "Mình đã tìm được thông tin."
                    )
                    return {
                        "reply": final_content,
                        "suggestions": ["Đặt lịch khám", "Xem quy trình khám bệnh"],
                    }

            messages.append(ai_response)

            proposal_result = None
            for call in tool_calls:
                tool_name = call["name"]
                tool_args = call.get("args", {}) or {}
                call_id = call.get("id", tool_name)

                if tool_name == "book_appointment":
                    try:
                        validated = BookAppointmentInput(**tool_args)
                        proposal_result = await self._propose_booking(
                            session_id, validated.model_dump()
                        )
                    except ValidationError:
                        logger.warning("Invalid booking args: %s", tool_args)
                        proposal_result = {
                            "reply": "Thông tin đặt lịch chưa hợp lệ, bạn vui lòng chọn lại khung giờ.",
                            "suggestions": ["Xem lịch trống bác sĩ", "Tìm bác sĩ khác"],
                        }

                    messages.append(
                        ToolMessage(
                            content=json.dumps(
                                {"status": "proposed"}, ensure_ascii=False
                            ),
                            tool_call_id=call_id,
                        )
                    )
                    continue

                try:
                    tool_result = await self._execute_read_tool(tool_name, tool_args, chat_history)
                except Exception:
                    logger.exception("Tool %s lỗi với args %s", tool_name, tool_args)
                    tool_result = {"error": "Không lấy được dữ liệu, vui lòng thử lại."}

                if tool_name == "search_doctors" and tool_result.get("found"):
                    return {
                        "reply": tool_result["formatted_text"],
                        "suggestions": ["Xem lịch trống", "Đặt lịch khám"],
                    }

                messages.append(
                    ToolMessage(
                        content=json.dumps(
                            tool_result, ensure_ascii=False, default=str
                        ),
                        tool_call_id=call_id,
                    )
                )

            if proposal_result is not None:
                return proposal_result

        try:
            final = await asyncio.wait_for(
                self.llm.ainvoke(messages),
                timeout=60.0
            )
            final_content = final.content if hasattr(final, "content") else ""
        except asyncio.TimeoutError:
            logger.error("LLM timeout ở lượt tổng hợp cuối")
            final_content = ""
        final_content = self._replace_hallucination(final_content)
        return {
            "reply": final_content
            or "Mình đã tìm được thông tin, bạn cần hỗ trợ thêm gì không?",
            "suggestions": [
                "Đặt lịch khám",
                "Xem quy trình khám bệnh",
                "Liên hệ hotline",
            ],
        }

    async def _execute_read_tool(self, tool_name: str, args: dict, chat_history: list[Any] | None = None) -> Any:
        logger.info(f"=== EXECUTE TOOL: {tool_name} ===")
        logger.info(f"=== TOOL ARGS: {args} ===")

        if tool_name == "search_doctors":
            try:
                validated = SearchDoctorsInput(**args)
            except ValidationError:
                logger.warning("Invalid search args: %s", args)
                return {"error": "Thông tin tìm kiếm chưa hợp lệ."}

            doctors, found = await self.doctor_search.search(
                specialty_name=validated.specialty_name,
                max_fee=validated.max_fee,
                doctor_name=validated.doctor_name,
            )

            if not found:
                if validated.specialty_name:
                    message = f"Không tìm thấy bác sĩ thuộc chuyên khoa '{validated.specialty_name}'."
                elif validated.doctor_name:
                    message = f"Không tìm thấy bác sĩ tên '{validated.doctor_name}'."
                elif validated.max_fee:
                    message = f"Không tìm thấy bác sĩ có giá khám dưới {validated.max_fee:,.0f} VND."
                else:
                    message = "Không tìm thấy bác sĩ phù hợp."
                return {"found": False, "message": message}

            doctors_list = []
            for idx, d in enumerate(doctors, 1):
                doctors_list.append(
                    {
                        "stt": idx,
                        "doctor_id": d.id,
                        "name": d.user.full_name if d.user else f"Bác sĩ #{d.id}",
                        "specialty": d.specialty.name if d.specialty else "Đa Khoa",
                        "fee": float(d.consultation_fee) if d.consultation_fee else 0.0,
                    }
                )

            formatted_lines = []
            for idx, d in enumerate(doctors_list, 1):
                formatted_lines.append(
                    f"{idx}. Bác sĩ [#{d['doctor_id']}] {d['name']} - {d['specialty']} - "
                    f"{d['fee']:,.0f} VND".replace(",", ".")
                )
            formatted_text = "\n".join(formatted_lines)

            return {
                "found": True,
                "doctors": doctors_list,
                "formatted_text": formatted_text,
            }

        if tool_name == "check_availability":
            try:
                validated = CheckAvailabilityInput(**args)
            except ValidationError:
                logger.warning("Invalid availability args: %s", args)
                return {"error": "Thông tin kiểm tra lịch chưa hợp lệ."}

            try:
                work_date = date.fromisoformat(validated.work_date)
            except ValueError:
                return {"error": "Ngày không hợp lệ, cần định dạng YYYY-MM-DD."}

            doctor_id = validated.doctor_id
            doctor_exists = await self._verify_doctor_exists(doctor_id)

            if not doctor_exists:
                logger.warning(
                    f"Doctor ID {doctor_id} không tồn tại, thử parse từ history"
                )

                doctor_id_from_history = self._parse_doctor_id_from_history(
                    chat_history
                )

                if doctor_id_from_history:
                    logger.info(
                        f"Đã tìm thấy doctor_id={doctor_id_from_history} từ history"
                    )
                    doctor_id = doctor_id_from_history
                else:
                    doctor_name_from_history = self._extract_doctor_name_from_history(
                        chat_history
                    )
                    if doctor_name_from_history:
                        corrected_id = await self._find_doctor_id_by_name(doctor_name_from_history)
                        if corrected_id:
                            logger.info(f"Đã tìm thấy doctor_id={corrected_id} cho tên '{doctor_name_from_history}'")
                            doctor_id = corrected_id
                        else:
                            return {"error": f"Không tìm thấy bác sĩ với tên '{doctor_name_from_history}'."}
                    else:
                        return {"error": "Không tìm thấy bác sĩ với ID đã cho."}

            data = await self.appointment_service.get_doctor_availability(
                doctor_id=doctor_id,
                work_date=work_date,
            )
            slots = data.get("available_slots", [])
            return {
                "doctor_id": data["doctor_id"],
                "doctor_name": data["doctor_name"],
                "specialty": data["specialty"],
                "work_date": str(data["work_date"]),
                "available_slots": [
                    {
                        "slot_id": s.id,
                        "start_time": str(getattr(s, "start_time", "")),
                        "end_time": str(getattr(s, "end_time", "")),
                    }
                    for s in slots
                ],
            }

        if tool_name == "list_specialties":
            specialties: list[
                Specialty
            ] = await self.specialty_service.get_specialties()
            return {
                "specialties": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "description": getattr(s, "description", None),
                    }
                    for s in specialties
                ]
            }

        if tool_name == "search_hospital_knowledge":
            try:
                validated = SearchKnowledgeInput(**args)
            except ValidationError:
                logger.warning("Invalid RAG args: %s", args)
                return {"found": False, "message": "Câu hỏi tra cứu chưa hợp lệ."}

            context = await self.rag_service.search(validated.query)
            if not context:
                return {
                    "found": False,
                    "message": "DỪNG LẠI. Không tìm thấy thông tin trong tài liệu. "
                               "HÃY TRẢ LỜI NGƯỜI DÙNG ĐÚNG CÂU NÀY: 'Tôi không tìm thấy thông tin về yêu cầu này trong tài liệu hiện có. "
                               "Vui lòng liên hệ trực tiếp bệnh viện để được hỗ trợ chính xác.' "
                               "KHÔNG được nói là bạn sẽ đi tìm thêm hoặc sẽ gọi tool."
                }

            return {"found": True, "context": context}

        raise ValueError(f"Tool không xác định: {tool_name}")

    async def _propose_booking(self, session_id: int, validated_data: dict) -> dict:
        slot_id = validated_data.get("slot_id")
        reason = validated_data.get("reason")

        if not slot_id:
            return {
                "reply": "Bạn muốn đặt khung giờ nào? Vui lòng cho mình biết khung giờ cụ thể.",
                "suggestions": ["Xem lịch trống bác sĩ"],
            }

        _pending_bookings[session_id] = {"slot_id": slot_id, "reason": reason}

        reply = f"Bạn xác nhận đặt khung giờ khám mã #{slot_id}"
        if reason:
            reply += f" (lý do: {reason})"
        reply += "?\n\nTrả lời 'xác nhận' để mình đặt lịch, hoặc 'hủy' nếu bạn đổi ý."

        return {"reply": reply, "suggestions": ["Xác nhận", "Hủy"]}


class ChatSessionService:
    def __init__(
        self,
        session_repo: ChatSessionRepoDep,
        message_repo: ChatMessageRepoDep,
        ai_chat_service: "AIChatService",
        agent_chat_service: "AgentChatService",
    ) -> None:
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.ai_chat_service = ai_chat_service
        self.agent_chat_service = agent_chat_service


    def _format_doctors_response(self, doctors: list[Doctor]) -> str:
        if not doctors:
            return "Không tìm thấy bác sĩ phù hợp với yêu cầu của bạn."
        lines = ["Danh sách bác sĩ phù hợp tại Bệnh viện Bạch Mai:"]
        for doc in doctors[:5]:
            s_name = doc.specialty.name if doc.specialty else "Đa Khoa"
            name = doc.user.full_name if doc.user else f"Bác sĩ ID {doc.id}"
            degree = doc.degree or "Bác sĩ"
            fee = float(doc.consultation_fee) if doc.consultation_fee else 0.0
            lines.append(f"- {degree} {name} | Chuyên khoa: {s_name} | Giá khám: {fee:,.0f} VNĐ")
        return "\n".join(lines)

    def _build_not_found_message(
            self, specialty: Optional[str], max_fee: Optional[float], doctor_name: Optional[str]
    ) -> str:
        if doctor_name:
            reason = f"Không tìm thấy bác sĩ '{doctor_name}' trong hệ thống của Bệnh viện Bạch Mai."
        elif specialty and max_fee:
            reason = f"Hiện không có bác sĩ nào thuộc chuyên khoa '{specialty}' có giá khám dưới {max_fee:,.0f} VNĐ."
        elif specialty:
            reason = f"Không tìm thấy bác sĩ nào thuộc chuyên khoa '{specialty}' trong cơ sở dữ liệu."
        elif max_fee:
            reason = f"Hiện không có bác sĩ nào có giá khám dưới {max_fee:,.0f} VNĐ."
        else:
            reason = "Không tìm thấy bác sĩ phù hợp với yêu cầu của bạn."
        return f"{reason} Bạn nên đến Khoa Khám bệnh (78 Giải Phóng, Hà Nội) để đăng ký khám theo diện BHYT hoặc khám thông thường."
    


    async def create_session(
        self, current_user: User, title: str | None = None
    ) -> ChatSession:
        session = ChatSession(
            user_id=current_user.id, title=title or "Cuộc trò chuyện mới"
        )
        return await self.session_repo.create(session)

    async def get_user_sessions(self, current_user: User) -> list[ChatSession]:
        return await self.session_repo.get_by_user(current_user.id)

    async def get_owned_session(
        self, session_id: int, current_user: User
    ) -> ChatSession:
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            raise ResourceNotFound("Không tìm thấy phiên chat")
        if session.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Bạn không có quyền truy cập phiên chat này")
        return session

    async def send_message(
            self, session_id: int, current_user: User, content: str
    ) -> dict:
        session = await self.get_owned_session(session_id, current_user)

        history = await self.message_repo.get_by_session(session_id)
        chat_history = [{"role": m.role, "content": m.content} for m in history]

        user_message = await self.message_repo.create(
            ChatMessage(session_id=session.id, role="user", content=content)
        )

        result = await self.agent_chat_service.chat(
            session_id=session_id,
            user_message=content,
            chat_history=chat_history,
            current_user=current_user,
        )

        assistant_message = await self.message_repo.create(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=result["reply"]
            )
        )

        session.updated_date = datetime.now()
        if session.title is None or session.title == "Cuộc trò chuyện mới":
            session.title = content[:50]
        await self.session_repo.update(session)

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "suggestions": result.get("suggestions", []),
        }

    async def get_session_messages(
        self, session_id: int, current_user: User
    ) -> list[ChatMessage]:
        await self.get_owned_session(session_id, current_user)
        return await self.message_repo.get_by_session(session_id)

    async def delete_session(self, session_id: int, current_user: User) -> None:
        session = await self.get_owned_session(session_id, current_user)
        await self.session_repo.delete(session.id)