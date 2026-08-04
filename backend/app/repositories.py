from datetime import date
from typing import Generic, TypeVar

from sqlalchemy import exists, func, select
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
        return data

    async def update(self, data: ModelType) -> ModelType:
        await self.db.flush()
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
                selectinload(Appointment.slot),
            )
        )
        return list(result.scalars().all())

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
                selectinload(Appointment.slot),
            )
        )
        return list(result.scalars().all())

    async def get_by_id_with_relations(self, appointment_id: int):
        result = await self.db.execute(
            select(Appointment)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.slot)
                .selectinload(ScheduleSlot.schedule)
                .selectinload(Schedule.doctor)
                .selectinload(Doctor.user),
            )
            .where(Appointment.id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slot_id(self, slot_id: int) -> Appointment | None:
        result = await self.db.execute(
            select(Appointment).where(Appointment.slot_id == slot_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_slot(self, appointment_id: int):
        result = await self.db.execute(
            select(Appointment)
            .options(selectinload(Appointment.slot))
            .where(Appointment.id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def cancel(self, appointment: Appointment, cancel_reason: str) -> Appointment:
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancel_reason = cancel_reason
        appointment.slot.status = ScheduleSlotStatus.AVAILABLE
        await self.db.flush()
        return appointment

    async def update_status(
        self, appointment: Appointment, new_status: AppointmentStatus
    ) -> Appointment:
        appointment.status = new_status
        await self.db.flush()
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

    async def get_active_by_id(
        self,  medicine_id: int
    ) -> Medicine | None:
        result = await self.db.execute(
            select(Medicine).where(
                Medicine.id == medicine_id, Medicine.status == "active"
            )
        )
        return result.scalar_one_or_none()


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Payment, db)

    async def get_by_appointment(self, appointment_id: int) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.appointment_id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_patient_id(self, patient_id: int) -> list[Payment]:
        result = await self.db.execute(
            select(Payment)
            .join(Appointment, Payment.appointment_id == Appointment.id)
            .where(Appointment.patient_id == patient_id)
            .order_by(Payment.created_date.desc())
        )
        return list(result.scalars().all())