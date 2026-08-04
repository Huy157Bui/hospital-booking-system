from datetime import UTC, datetime, timedelta, date
from typing import Annotated
from fastapi import Depends
from jose import jwt, JWTError
from passlib.context import CryptContext
from passlib.exc import InvalidTokenError
from sqlalchemy import DECIMAL
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.exceptions import (
    BadRequestException,
    ForbiddenException,
    ResourceNotFound,
    ConflictException,
)
from app.models import (
    Payment,
    Appointment,
    AppointmentStatus,
    Doctor,
    Patient,
    ScheduleSlot,
    ScheduleSlotStatus,
    Specialty,
    User,
    UserRole,
    Medicine,
    MedicalRecord,
    Examination,
    PrescriptionDetail,
    Prescription,
    PaymentStatus,
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
    ExaminationOut,
    PaymentOut,
)
from app.dependencies.repos import *
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
    def __init__(
        self,
        user_repo: UserRepoDep,
    ):
        self.user_repo = user_repo

    def decode_token(self, token: str) -> int:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except JWTError:
            raise InvalidTokenError()
        user_id = payload.get("id")
        if user_id is None:
            raise InvalidTokenError()
        return user_id

    async def get_current_user(self, token: str) -> User:
        user_id = self.decode_token(token)
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError()
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
        return await self.user_repo.create(user)

    async def authenticate(self, username: str, password: str) -> User | None:
        user = await self.user_repo.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
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
            data={"sub": user.username, "id": user.id, "role": user.role.value}
        )
        return {"access_token": access_token, "token_type": "bearer", "user": user}

    async def get_user_by_username(self, username: str) -> User | None:
        user = await self.user_repo.get_by_username(username)
        if user is None:
            return None
        if not user.is_active:
            return None
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return None
        if not user.is_active:
            return None
        return user


class UserService:
    def __init__(
        self,
        user_repo: UserRepoDep,
    ):
        self.user_repo = user_repo

    def get_profile(self, current_user: User):
        return current_user


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

        raise ForbiddenException("Chỉ bệnh nhân, bác sĩ hoặc quản trị viên mới được xem lịch hẹn này")

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

        if getattr(slot, "appointment", None) is not None:
            raise ConflictException("Khung giờ đã được đặt")

        existing = await self.appointment_repo.get_by_slot_id(appointment_data.slot_id)
        if existing is not None:
            raise ConflictException("Khung giờ đã được đặt")

        appointment = Appointment(
            patient_id=patient.id,
            slot_id=slot.id,
            status=AppointmentStatus.PENDING,
        )
        await self.appointment_repo.create(appointment)

        slot.status = ScheduleSlotStatus.BOOKED
        slot.appointment = appointment

        await self.appointment_repo.commit()
        await self.appointment_repo.refresh(appointment)

        return appointment

    async def cancel_appointment(
        self,
        appointment_id: int,
        current_user: User,
        cancel_data: AppointmentCancel,
    ):
        appointment = await self.appointment_repo.get_by_id_with_slot(appointment_id)
        if not appointment:
            raise ResourceNotFound("Không tìm thấy lịch hẹn")

        if current_user.role != UserRole.ADMIN:
            if current_user.role != UserRole.PATIENT:
                raise ForbiddenException("Từ chối truy cập")
            patient = await self.patient_repo.get_by_user_id(current_user.id)
            if not patient or appointment.patient_id != patient.id:
                raise ForbiddenException("Từ chối truy cập")

        if appointment.status == AppointmentStatus.CANCELLED:
            raise ForbiddenException("Từ chối truy cập")
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

        appointment = await self.appointment_repo.get_by_id_with_slot(appointment_id)
        if not appointment:
            raise ResourceNotFound("Không tìm thấy lịch hẹn")

        if appointment.slot.schedule.doctor_id != doctor.id:
            raise ForbiddenException("Bạn không phải bác sĩ được phân công cho lịch hẹn này")

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
        updated = await self.appointment_repo.get_by_id_with_relations(appointment_id)
        if not updated:
            raise ResourceNotFound("Không tìm thấy lịch hẹn sau khi cập nhật")
        return updated

    async def get_available_slots(
        self, doctor_id: int, date: date
    ) -> list[ScheduleSlot]:
        slots = await self.slot_repo.get_available_slots_by_doctor_and_date(
            doctor_id, date
        )
        return slots

    async def add_examination_record(
        self,
        appointment_id: int,
        doctor: Doctor,
        data: ExaminationRecordCreate,
    ) -> Examination:
        appointment = await self.appointment_repo.get_by_id_with_slot(appointment_id)
        if not appointment:
            raise ResourceNotFound("Không tìm thấy lịch hẹn")
        if appointment.slot.schedule.doctor_id != doctor.id:
            raise ForbiddenException("Bạn không phải bác sĩ được phân công")
        if appointment.status not in (
            AppointmentStatus.EXAMINING,
            AppointmentStatus.COMPLETED,
        ):
            raise BadRequestException("Không thể thêm hồ sơ cho trạng thái này")

        patient = appointment.patient
        if not patient:
            raise ResourceNotFound("Không tìm thấy bệnh nhân")

        medical_record = await self.medical_record_repo.get_by_patient_id(patient.id)
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
                        total_amount=DECIMAL(0),
                        status=0,
                    )
                )

                total = DECIMAL(0)
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

        await self.examination_repo.commit()
        await self.examination_repo.refresh(examination)
        return examination

    async def get_appointment_record(self, appointment: Appointment) -> Examination:
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
            raise BadRequestException("Chỉ có thể tạo thanh toán cho lịch hẹn đã hoàn thành hoặc đang chờ xác nhận")

        existing_payment = await self.payment_repo.get_by_appointment(appointment_id)
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
        await self.payment_repo.commit()
        await self.payment_repo.refresh(payment)

        appointment.status = AppointmentStatus.PAID
        await self.appointment_repo.update(appointment)

        return payment


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

    async def create_specialty(self, specialty_data: SpecialtyCreate) -> Specialty:
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
    ) -> None:
        self.doctor_repo = doctor_repo
        self.user_repo = user_repo
        self.specialty_repo = specialty_repo
        self.schedule_repo = schedule_repo
        self.appointment_repo = appointment_repo
        self.slot_repo = slot_repo

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
        schedules = await self.schedule_repo.get_by_doctor(doctor_id)
        return schedules

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
        if current_user.role == UserRole.ADMIN:
            pass
        elif current_user.role == UserRole.DOCTOR:
            doctor = await self.doctor_repo.get_by_user_id(current_user.id)
            if not doctor:
                raise ResourceNotFound("Không tìm thấy hồ sơ bác sĩ")
            has_access = await self.appointment_repo.exists_by_doctor_and_patient(
                doctor.id, patient_id
            )
            if not has_access:
                raise ForbiddenException("Bạn không có quyền xem hồ sơ bệnh án của bệnh nhân này")
        else:
            raise ForbiddenException("Chỉ bác sĩ và quản trị viên mới có quyền truy cập")
        medical_record = await self.medical_record_repo.get_by_patient_id(patient_id)
        examinations = await self.examination_repo.get_by_patient(patient_id)
        return {"medical_record": medical_record, "examinations": examinations}


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
            raise ForbiddenException("Bạn không thể truy cập khung giờ của bác sĩ khác")
        return slot

class PaymentService:
    def __init__(
            self,
            payment_repo: PaymentRepoDep,
    ):
        self.payment_repo = payment_repo

    async def get_user_payments(self, current_user: User) -> list[PaymentOut]:
        if current_user.role != UserRole.PATIENT:
            raise ValueError("Chỉ bệnh nhân mới được xem lịch sử thanh toán", 403)
        payments = await self.payment_repo.get_by_patient_id(current_user.id)
        return [PaymentOut.model_validate(p) for p in payments]