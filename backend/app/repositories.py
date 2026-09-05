import logging

from app.schemas import PaymentOut

logger = logging.getLogger(__name__)

from datetime import date, datetime
from typing import Generic, TypeVar, cast

from sqlalchemy import exists, func, select, distinct, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.base import Base
from app.models import (
    Payment,
    Appointment,
    AppointmentStatus,
    Doctor,
    Examination,
    MedicalRecord,
    Medicine,
    Patient,
    Prescription,
    PrescriptionDetail,
    Schedule,
    ScheduleSlot,
    ScheduleSlotStatus,
    ScheduleStatus,
    Specialty,
    User,
    SpecialtyStatus,
    PaymentStatus,
    ChatSession,
    ChatMessage,
    RefreshToken,
)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> ModelType | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, *, skip: int = 0, limit: int = 100):
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, data: ModelType) -> ModelType:
        self.db.add(data)
        await self.db.flush()
        await self.db.refresh(data)
        return data

    async def update(self, data: ModelType) -> ModelType:
        await self.db.flush()
        await self.db.refresh(data)
        return data

    async def delete(self, id: int) -> None:
        obj = await self.get_by_id(id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()

    async def count(self) -> int:
        result = await self.db.execute(select(self.model))
        return len(result.scalars().all())

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def refresh(self, obj: ModelType) -> None:
        await self.db.refresh(obj)


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_active_users(self, *, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


class PatientRepository(BaseRepository[Patient]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Patient, db)

    async def get_by_identity_number(self, identity: str) -> Patient | None:
        result = await self.db.execute(
            select(Patient)
            .where(Patient.identity_number == identity)
            .options(selectinload(Patient.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Patient | None:
        result = await self.db.execute(
            select(Patient)
            .where(Patient.id == user_id)
            .options(selectinload(Patient.user))
        )
        return result.scalar_one_or_none()


class DoctorRepository(BaseRepository[Doctor]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Doctor, db)

    async def search_doctors_with_filters(
        self,
        max_fee: float | None = None,
        limit: int | None = None,
    ) -> list[Doctor]:
        stmt = (
            select(Doctor)
            .where(Doctor.status == "active")
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )

        if max_fee and max_fee > 0:
            stmt = stmt.where(Doctor.consultation_fee <= max_fee)

        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_license(self, license_number: str) -> Doctor | None:
        result = await self.db.execute(
            select(Doctor)
            .where(Doctor.license_number == license_number)
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return result.scalar_one_or_none()

    async def get_by_specialty(
        self, specialty_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Doctor]:
        result = await self.db.execute(
            select(Doctor)
            .where(Doctor.specialty_id == specialty_id, Doctor.status == "active")
            .offset(skip)
            .limit(limit)
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return list(result.scalars().all())

    async def get_active_doctors(self) -> list[Doctor]:
        result = await self.db.execute(
            select(Doctor)
            .where(Doctor.status == "active")
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return list(result.scalars().all())

    async def get_active_doctors_by_specialty(self, specialty_id: int) -> list[Doctor]:
        result = await self.db.execute(
            select(Doctor)
            .where(Doctor.status == "active", Doctor.specialty_id == specialty_id)
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return list(result.scalars().all())

    async def get_active_by_id(self, doctor_id: int) -> Doctor | None:
        result = await self.db.execute(
            select(Doctor)
            .where(Doctor.id == doctor_id, Doctor.status == "active")
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Doctor | None:
        result = await self.db.execute(
            select(Doctor)
            .where(Doctor.id == user_id)
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return result.scalar_one_or_none()

    async def count_active_by_specialty(self, specialty_id: int) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Doctor)
            .where(Doctor.specialty_id == specialty_id, Doctor.status == "active")
        )
        return result.scalar_one()

    async def exists_active_by_specialty(self, specialty_id: int) -> bool:
        stmt = select(
            exists().where(
                Doctor.specialty_id == specialty_id, Doctor.status == "active"
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def search_doctors_for_ai(
        self, specialty_name: str | None = None, max_fee: float | None = None
    ) -> list[Doctor]:
        stmt = (
            select(Doctor)
            .join(Specialty)
            .options(
                selectinload(Doctor.specialty),
                selectinload(
                    Doctor.user
                ),
            )
        )

        if specialty_name:
            stmt = stmt.where(Specialty.name.ilike(f"%{specialty_name}%"))

        if max_fee and max_fee > 0:
            stmt = stmt.where(Doctor.consultation_fee <= max_fee)

        stmt = stmt.limit(5)

        result = await self.db.execute(stmt)
        doctors = result.scalars().all()

        if not doctors and specialty_name:
            stmt_fb1 = (
                select(Doctor)
                .join(Specialty)
                .options(selectinload(Doctor.specialty), selectinload(Doctor.user))
                .where(Specialty.name.ilike(f"%{specialty_name}%"))
                .limit(5)
            )
            res_fb1 = await self.db.execute(stmt_fb1)
            doctors = res_fb1.scalars().all()

        if not doctors:
            stmt_fb2 = (
                select(Doctor)
                .options(selectinload(Doctor.specialty), selectinload(Doctor.user))
                .order_by(Doctor.consultation_fee.asc())
                .limit(5)
            )
            res_fb2 = await self.db.execute(stmt_fb2)
            doctors = res_fb2.scalars().all()

        return doctors


class SpecialtyRepository(BaseRepository[Specialty]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Specialty, db)

    async def get_by_name(self, name: str) -> Specialty | None:
        result = await self.db.execute(select(Specialty).where(Specialty.name == name))
        return result.scalar_one_or_none()

    async def get_active_specialties(self) -> list[Specialty]:
        result = await self.db.execute(
            select(Specialty)
            .where(Specialty.status == "active")
            .order_by(Specialty.name)
        )
        return list(result.scalars().all())

    async def get_active_by_id(self, specialty_id: int) -> Specialty | None:
        result = await self.db.execute(
            select(Specialty).where(
                Specialty.id == specialty_id, Specialty.status == "active"
            )
        )
        return result.scalar_one_or_none()

    # che
    async def toggle_status(self, specialty: Specialty) -> Specialty:
        if specialty.status == SpecialtyStatus.ACTIVE:
            specialty.status = SpecialtyStatus.INACTIVE
        else:
            specialty.status = SpecialtyStatus.ACTIVE
        return await self.update(specialty)


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Schedule, db)


    async def get_doctor_available_schedule(
            self, doctor_id: int, from_date: date | None = None
    ) -> list[Schedule]:
        if from_date is None:
            from_date = date.today()

        stmt = (
            select(Schedule)
            .where(
                Schedule.doctor_id == doctor_id,
                Schedule.work_date >= from_date,
                Schedule.status == ScheduleStatus.OPEN,
            )
            .options(
                selectinload(Schedule.doctor).selectinload(Doctor.user),
                selectinload(Schedule.doctor).selectinload(Doctor.specialty),
                selectinload(Schedule.slots),
            )
            .order_by(Schedule.work_date)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_doctor(self, doctor_id: int) -> list[Schedule]:
        result = await self.db.execute(
            select(Schedule)
            .where(Schedule.doctor_id == doctor_id)
            .options(
                selectinload(Schedule.doctor).selectinload(Doctor.user),
                selectinload(Schedule.doctor).selectinload(Doctor.specialty),
                selectinload(Schedule.slots),
            )
        )
        return list(result.scalars().all())

    async def get_by_doctor_and_date(
        self, doctor_id: int, work_date: date
    ) -> list[Schedule]:
        result = await self.db.execute(
            select(Schedule)
            .where(Schedule.doctor_id == doctor_id, Schedule.work_date == work_date)
            .options(
                selectinload(Schedule.doctor).selectinload(Doctor.user),
                selectinload(Schedule.doctor).selectinload(Doctor.specialty),
                selectinload(Schedule.slots),
            )
        )
        return list(result.scalars().all())

    async def get_open_schedules(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[Schedule]:
        result = await self.db.execute(
            select(Schedule)
            .where(Schedule.status == ScheduleStatus.OPEN)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Schedule.doctor).selectinload(Doctor.user),
                selectinload(Schedule.doctor).selectinload(Doctor.specialty),
                selectinload(Schedule.slots),
            )
        )
        return list(result.scalars().all())


class ScheduleSlotRepository(BaseRepository[ScheduleSlot]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ScheduleSlot, db)

    async def get_by_schedule(
        self,
        schedule_id: int,
    ) -> list[ScheduleSlot]:
        result = await self.db.execute(
            select(ScheduleSlot).where(ScheduleSlot.schedule_id == schedule_id)
        )
        return list(result.scalars().all())

    async def get_by_id_with_schedule(self, slot_id: int) -> ScheduleSlot | None:
        result = await self.db.execute(
            select(ScheduleSlot)
            .where(ScheduleSlot.id == slot_id)
            .options(selectinload(ScheduleSlot.schedule))
        )
        return result.scalar_one_or_none()

    async def get_available_slots_by_doctor_and_date(
        self, doctor_id: int, date: date
    ) -> list[ScheduleSlot]:
        statement = (
            select(ScheduleSlot)
            .join(Schedule)
            .where(
                Schedule.doctor_id == doctor_id,
                Schedule.date == date,
                Schedule.status == ScheduleSlotStatus.AVAILABLE,
            )
            .order_by(ScheduleSlot.start_time)
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def get_available_slots_by_doctor_and_date(
        self, doctor_id: int, work_date: date
    ) -> list[ScheduleSlot]:
        stmt = (
            select(ScheduleSlot)
            .join(Schedule)
            .where(
                Schedule.doctor_id == doctor_id,
                Schedule.work_date == work_date,
                Schedule.status == ScheduleStatus.OPEN,
                ScheduleSlot.status == ScheduleSlotStatus.AVAILABLE,
            )
            .options(
                selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
                selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.specialty),
            )
            .order_by(ScheduleSlot.start_time)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Appointment, db)

    async def get_by_patient(
        self, patient_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Appointment]:
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.specialty),
            )
        )
        return list(result.scalars().unique().all())

    async def get_by_doctor(
        self, doctor_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Appointment]:
        result = await self.db.execute(
            select(Appointment)
            .join(Appointment.slot)
            .join(ScheduleSlot.schedule)
            .where(Schedule.doctor_id == doctor_id)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.specialty),
            )
        )
        return list(result.scalars().unique().all())

    async def get_by_id_with_relations(self, appointment_id: int):
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.id == appointment_id)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.specialty),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_slot_id(self, slot_id: int) -> Appointment | None:
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.slot_id == slot_id,
                Appointment.status != AppointmentStatus.CANCELLED,
                )
        )
        return result.scalar_one_or_none()

    async def create_with_slot(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        await self.db.flush()
        slot_stmt = select(ScheduleSlot).where(ScheduleSlot.id == appointment.slot_id)
        slot_result = await self.db.execute(slot_stmt)
        slot = slot_result.scalar_one()
        slot.status = ScheduleSlotStatus.BOOKED
        await self.db.flush()
        stmt = (
            select(Appointment)
            .where(Appointment.id == appointment.id)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.specialty),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id_with_slot(self, appointment_id: int):
        stmt = (
            select(Appointment)
            .options(
                selectinload(Appointment.patient),
                selectinload(Appointment.slot).selectinload(ScheduleSlot.schedule),
            )
            .where(Appointment.id == appointment_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_doctor_id_by_slot(self, slot_id: int) -> int | None:
        stmt = (
            select(Schedule.doctor_id)
            .join(ScheduleSlot, ScheduleSlot.schedule_id == Schedule.id)
            .where(ScheduleSlot.id == slot_id)
        )
        result = await self.db.execute(stmt)
        doctor_id = result.scalar_one_or_none()
        logger.info(f"  get_doctor_id_by_slot: slot_id={slot_id} → doctor_id={doctor_id}")
        return doctor_id

    async def get_slot_with_doctor(self, slot_id: int) -> dict | None:
        stmt = (
            select(ScheduleSlot, Schedule.doctor_id, Schedule.work_date)
            .join(Schedule, ScheduleSlot.schedule_id == Schedule.id)
            .where(ScheduleSlot.id == slot_id)
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if not row:
            return None
        slot, doctor_id, work_date = row
        return {
            "slot_id": slot.id,
            "doctor_id": doctor_id,
            "work_date": work_date,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "status": slot.status,
        }

    async def cancel(self, appointment: Appointment, cancel_reason: str) -> Appointment:
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancel_reason = cancel_reason
        appointment.slot.status = ScheduleSlotStatus.AVAILABLE
        await self.db.flush()

        stmt = (
            select(Appointment)
            .where(Appointment.id == appointment.id)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.specialty),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def update_status(
            self, appointment: Appointment, new_status: AppointmentStatus
    ) -> Appointment:
        appointment.status = new_status
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def exists_by_doctor_and_patient(
        self, doctor_id: int, patient_id: int
    ) -> bool:
        stmt = select(
            exists().where(
                Appointment.patient_id == patient_id,
                Appointment.slot.has(
                    ScheduleSlot.schedule.has(Schedule.doctor_id == doctor_id)
                ),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()


class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(MedicalRecord, db)

    async def get_by_patient_id(self, patient_id: int) -> MedicalRecord | None:
        result = await self.db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient_id)
            .options(selectinload(MedicalRecord.patient).selectinload(Patient.user))
        )
        return result.scalar_one_or_none()

    async def get_by_record_number(self, record_number: str) -> MedicalRecord | None:
        result = await self.db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.record_number == record_number)
            .options(selectinload(MedicalRecord.patient).selectinload(Patient.user))
        )
        return result.scalar_one_or_none()

    async def exists_by_patient(self, patient_id: int) -> bool:
        stmt = select(exists().where(MedicalRecord.patient_id == patient_id))
        result = await self.db.execute(stmt)
        return result.scalar_one()


class ExaminationRepository(BaseRepository[Examination]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Examination, db)

    @staticmethod
    def _examination_options():
        return [
            selectinload(Examination.appointment)
            .selectinload(Appointment.patient)
            .selectinload(Patient.user),
            selectinload(Examination.appointment).selectinload(Appointment.slot),
            selectinload(Examination.medical_record)
            .selectinload(MedicalRecord.patient)
            .selectinload(Patient.user),
            selectinload(Examination.patient).selectinload(Patient.user),
            selectinload(Examination.doctor).selectinload(Doctor.user),
            selectinload(Examination.doctor).selectinload(Doctor.specialty),
        ]

    async def get_by_appointment(self, appointment_id: int) -> Examination | None:
        result = await self.db.execute(
            select(Examination)
            .where(Examination.appointment_id == appointment_id)
            .options(*self._examination_options())
        )
        return result.scalar_one_or_none()

    async def get_by_patient(
        self, patient_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Examination]:
        result = await self.db.execute(
            select(Examination)
            .where(Examination.patient_id == patient_id)
            .offset(skip)
            .limit(limit)
            .options(*self._examination_options())
        )
        return list(result.scalars().all())

    async def get_by_doctor(
        self, doctor_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Examination]:
        result = await self.db.execute(
            select(Examination)
            .where(Examination.doctor_id == doctor_id)
            .offset(skip)
            .limit(limit)
            .options(*self._examination_options())
        )
        return list(result.scalars().all())

    async def get_by_medical_record(self, medical_record_id: int) -> list[Examination]:
        result = await self.db.execute(
            select(Examination)
            .where(Examination.medical_record_id == medical_record_id)
            .options(*self._examination_options())
        )
        return list(result.scalars().all())


class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Prescription, db)

    @staticmethod
    def _prescription_options():
        return [
            selectinload(Prescription.examination),
            selectinload(Prescription.prescription_details).selectinload(
                PrescriptionDetail.medicine
            ),
        ]

    async def get_by_examination(self, examination_id: int) -> list[Prescription]:
        result = await self.db.execute(
            select(Prescription)
            .where(Prescription.examination_id == examination_id)
            .options(*self._prescription_options())
        )
        return list(result.scalars().all())

    async def delete_many(self, prescriptions: list[Prescription]) -> None:
        for p in prescriptions:
            await self.db.delete(p)
        await self.db.flush()


class PrescriptionDetailRepository(BaseRepository[PrescriptionDetail]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(PrescriptionDetail, db)

    async def get_by_prescription(
        self, prescription_id: int
    ) -> list[PrescriptionDetail]:
        result = await self.db.execute(
            select(PrescriptionDetail)
            .where(PrescriptionDetail.prescription_id == prescription_id)
            .options(selectinload(PrescriptionDetail.medicine))
        )
        return list(result.scalars().all())

    async def get_by_medicine(
        self, medicine_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[PrescriptionDetail]:
        result = await self.db.execute(
            select(PrescriptionDetail)
            .where(PrescriptionDetail.medicine_id == medicine_id)
            .offset(skip)
            .limit(limit)
            .options(selectinload(PrescriptionDetail.medicine))
        )
        return list(result.scalars().all())

    async def bulk_create(
        self, details: list[PrescriptionDetail]
    ) -> list[PrescriptionDetail]:
        self.db.add_all(details)
        await self.db.flush()
        return details


class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Medicine, db)

    async def get_by_code(self, code: str) -> Medicine | None:
        result = await self.db.execute(select(Medicine).where(Medicine.code == code))
        return result.scalar_one_or_none()

    async def get_active_medicines(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[Medicine]:
        result = await self.db.execute(
            select(Medicine)
            .where(Medicine.status == "active")
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_by_code(self, code: str) -> Medicine | None:
        result = await self.db.execute(
            select(Medicine).where(Medicine.code == code, Medicine.status == "active")
        )
        return result.scalar_one_or_none()

    async def get_active_by_id(self, medicine_id: int) -> Medicine | None:
        result = await self.db.execute(
            select(Medicine).where(
                Medicine.id == medicine_id, Medicine.status == "active"
            )
        )
        return result.scalar_one_or_none()


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Payment, db)

    async def get_by_id_with_appointment(self, payment_id: int) -> Payment | None:
        result = await self.db.execute(
            select(Payment)
            .options(selectinload(Payment.appointment))
            .where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_appointment(self, appointment_id: int) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.appointment_id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_patient_id(self, patient_id: int) -> list[Payment]:
        stmt = (
            select(Payment)
            .join(Appointment, Payment.appointment_id == Appointment.id)
            .options(
                selectinload(Payment.appointment)
                .selectinload(Appointment.patient)
                .selectinload(Patient.user),
                selectinload(Payment.appointment)
                .selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
                selectinload(Payment.appointment)
                .selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.specialty),
            )
            .where(Appointment.patient_id == patient_id)
            .order_by(Payment.created_date.desc())
        )

        result = await self.db.execute(stmt)
        payments = list(result.scalars().all())
        result_out = []
        for p in payments:
            p_dict = p.__dict__.copy()
            appt = p.appointment

            if (
                appt
                and getattr(appt, "slot", None)
                and getattr(appt.slot, "schedule", None)
                and getattr(appt.slot.schedule, "doctor", None)
            ):

                doctor = appt.slot.schedule.doctor
                p_dict["appointment_summary"] = {
                    "id": appt.id,
                    "doctor_name": doctor.user.full_name if getattr(doctor, 'user', None) else "Chưa cập nhật",
                    "specialty_name": doctor.specialty.name if getattr(doctor, 'specialty', None) else "Chưa cập nhật",
                    "work_date": appt.slot.schedule.work_date,
                    "start_time": appt.slot.start_time
                }
            else:
                p_dict["appointment_summary"] = None

            result_out.append(PaymentOut.model_validate(p_dict))

        return result_out

    async def get_revenue_payments(
        self, start_date: datetime, end_date: datetime, doctor_id: int | None = None
    ) -> list[Payment]:
        query = (
            select(Payment)
            .join(Appointment, Payment.appointment_id == Appointment.id)
            .join(ScheduleSlot, Appointment.slot_id == ScheduleSlot.id)
            .join(Schedule, ScheduleSlot.schedule_id == Schedule.id)
            .join(Doctor, Schedule.doctor_id == Doctor.id)
            .where(
                Payment.status == PaymentStatus.SUCCESS,
                Payment.created_date >= start_date,
                Payment.created_date <= end_date,
            )
            .options(
                selectinload(Payment.appointment)
                .selectinload(Appointment.patient)
                .selectinload(Patient.user),
                selectinload(Payment.appointment)
                .selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
            )
            .order_by(Payment.created_date.desc())
        )

        if doctor_id is not None:
            query = query.where(Doctor.id == doctor_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

class ReportRepository(BaseRepository[Appointment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Appointment, db)

    async def get_patient_count_by_specialty(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[tuple[int, str, int]]:
        query = (
            select(
                Specialty.id,
                Specialty.name,
                func.count(distinct(Appointment.patient_id)).label("patient_count"),
            )
            .join(Doctor, Specialty.id == Doctor.specialty_id)
            .join(Schedule, Doctor.id == Schedule.doctor_id)
            .join(ScheduleSlot, Schedule.id == ScheduleSlot.schedule_id)
            .join(Appointment, ScheduleSlot.id == Appointment.slot_id)
            .where(Appointment.status.in_(["COMPLETED", "PAID"]))
        )

        if start_date:
            query = query.where(Appointment.created_date >= start_date)
        if end_date:
            query = query.where(Appointment.created_date <= end_date)

        query = query.group_by(Specialty.id, Specialty.name)
        result = await self.db.execute(query)
        return result.all()

    async def get_total_unique_patients(self, start_date=None, end_date=None) -> int:
        query = select(func.count(distinct(Appointment.patient_id))).where(
            Appointment.status.in_(
                [AppointmentStatus.COMPLETED, AppointmentStatus.PAID]
            )
        )
        if start_date:
            query = query.where(Appointment.created_date >= start_date)
        if end_date:
            query = query.where(Appointment.created_date <= end_date)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_appointment_summary(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ):
        conditions = []
        if start_date:
            conditions.append(Appointment.created_date >= start_date)
        if end_date:
            conditions.append(Appointment.created_date <= end_date)
        query_status = (
            select(Appointment.status, func.count().label("count"))
            .where(*conditions)
            .group_by(Appointment.status)
        )
        result_status = await self.db.execute(query_status)
        status_counts = result_status.all()

        query_daily = (
            select(
                cast(Appointment.created_date, Date).label("day"),
                Appointment.status,
                func.count().label("count"),
            )
            .where(*conditions)
            .group_by(cast(Appointment.created_date, Date), Appointment.status)
            .order_by("day")
        )
        result_daily = await self.db.execute(query_daily)
        daily_rows = result_daily.all()

        query_total = select(func.count()).select_from(Appointment).where(*conditions)
        total = await self.db.scalar(query_total)

        return {
            "total": total,
            "status_counts": status_counts,
            "daily_rows": daily_rows
        }

class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ChatSession, db)

    async def get_by_user(self, user_id: int) -> list[ChatSession]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_date.desc())
        )
        return list(result.scalars().all())


class ChatMessageRepository(BaseRepository[ChatMessage]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ChatMessage, db)

    async def get_by_session(self, session_id: int) -> list[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_date.asc())
        )
        return list(result.scalars().all())

class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(RefreshToken, db)

    async def revoke(self, token: RefreshToken) -> RefreshToken:
        token.revoked = True
        return await self.update(token)

    async def revoke_all_for_user(self, user_id: int) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
        await self.db.flush()