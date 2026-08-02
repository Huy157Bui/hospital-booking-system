from datetime import date
from typing import Generic, TypeVar

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.base import Base
from app.models import (
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
)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> ModelType | None:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession, *, skip: int = 0, limit: int = 100):
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, data: ModelType) -> ModelType:
        db.add(data)
        await db.commit()
        await db.refresh(data)
        return data

    async def update(self, db: AsyncSession, data: ModelType) -> ModelType:
        await db.commit()
        await db.refresh(data)
        return data

    async def delete(self, db: AsyncSession, id: int) -> ModelType | None:
        obj = await self.get_by_id(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def count(self, db: AsyncSession) -> int:
        result = await db.execute(select(self.model))
        return len(result.scalars().all())


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_active_users(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[User]:
        result = await db.execute(
            select(User).where(User.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


class PatientRepository(BaseRepository[Patient]):
    def __init__(self):
        super().__init__(Patient)

    async def get_by_identity_number(
        self, db: AsyncSession, identity: str
    ) -> Patient | None:
        result = await db.execute(
            select(Patient)
            .where(Patient.identity_number == identity)
            .options(selectinload(Patient.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Patient | None:
        result = await db.execute(
            select(Patient)
            .where(Patient.id == user_id)
            .options(selectinload(Patient.user))
        )
        return result.scalar_one_or_none()


class DoctorRepository(BaseRepository[Doctor]):
    def __init__(self):
        super().__init__(Doctor)

    async def get_by_license(
        self, db: AsyncSession, license_number: str
    ) -> Doctor | None:
        result = await db.execute(
            select(Doctor)
            .where(Doctor.license_number == license_number)
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return result.scalar_one_or_none()

    async def get_by_specialty(
        self, db: AsyncSession, specialty_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Doctor]:
        result = await db.execute(
            select(Doctor)
            .where(Doctor.specialty_id == specialty_id, Doctor.status == "active")
            .offset(skip)
            .limit(limit)
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return list(result.scalars().all())

    async def get_active_doctors(self, db: AsyncSession) -> list[Doctor]:
        result = await db.execute(
            select(Doctor)
            .where(Doctor.status == "active")
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return list(result.scalars().all())

    async def get_active_doctors_by_specialty(
        self, db: AsyncSession, specialty_id: int
    ) -> list[Doctor]:
        result = await db.execute(
            select(Doctor)
            .where(Doctor.status == "active", Doctor.specialty_id == specialty_id)
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return list(result.scalars().all())

    async def get_active_by_id(self, db: AsyncSession, doctor_id: int) -> Doctor | None:
        result = await db.execute(
            select(Doctor)
            .where(Doctor.id == doctor_id, Doctor.status == "active")
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Doctor | None:
        result = await db.execute(
            select(Doctor)
            .where(Doctor.id == user_id)
            .options(selectinload(Doctor.user), selectinload(Doctor.specialty))
        )
        return result.scalar_one_or_none()

    async def count_active_by_specialty(
        self, db: AsyncSession, specialty_id: int
    ) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(Doctor)
            .where(Doctor.specialty_id == specialty_id, Doctor.status == "active")
        )
        return result.scalar_one()

    async def exists_active_by_specialty(
        self, db: AsyncSession, specialty_id: int
    ) -> bool:
        stmt = select(
            exists().where(
                Doctor.specialty_id == specialty_id, Doctor.status == "active"
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one()


class SpecialtyRepository(BaseRepository[Specialty]):
    def __init__(self):
        super().__init__(Specialty)

    async def get_by_name(self, db: AsyncSession, name: str) -> Specialty | None:
        result = await db.execute(select(Specialty).where(Specialty.name == name))
        return result.scalar_one_or_none()

    async def get_active_specialties(self, db: AsyncSession) -> list[Specialty]:
        result = await db.execute(
            select(Specialty)
            .where(Specialty.status == "active")
            .order_by(Specialty.name)
        )
        return list(result.scalars().all())

    async def get_active_by_id(
        self, db: AsyncSession, specialty_id: int
    ) -> Specialty | None:
        result = await db.execute(
            select(Specialty).where(
                Specialty.id == specialty_id, Specialty.status == "active"
            )
        )
        return result.scalar_one_or_none()

    async def toggle_status(self, db: AsyncSession, specialty: Specialty) -> Specialty:
        if specialty.status == "active":
            specialty.status = "inactive"
        else:
            specialty.status = "active"
        return await self.update(db, specialty)


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self):
        super().__init__(Schedule)

    async def get_by_doctor(self, db: AsyncSession, doctor_id: int) -> list[Schedule]:
        result = await db.execute(
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
        self, db: AsyncSession, doctor_id: int, work_date: date
    ) -> list[Schedule]:
        result = await db.execute(
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
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[Schedule]:
        result = await db.execute(
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
    def __init__(self):
        super().__init__(ScheduleSlot)

    async def get_by_schedule(
        self,
        db: AsyncSession,
        schedule_id: int,
    ) -> list[ScheduleSlot]:
        result = await db.execute(
            select(ScheduleSlot).where(ScheduleSlot.schedule_id == schedule_id)
        )
        return list(result.scalars().all())

    async def get_by_id_with_schedule(
        self, db: AsyncSession, slot_id: int
    ) -> ScheduleSlot | None:
        result = await db.execute(
            select(ScheduleSlot)
            .where(ScheduleSlot.id == slot_id)
            .options(selectinload(ScheduleSlot.schedule))
        )
        return result.scalar_one_or_none()


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self):
        super().__init__(Appointment)

    async def get_by_patient(
        self, db: AsyncSession, patient_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Appointment]:
        result = await db.execute(
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
        self, db: AsyncSession, doctor_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Appointment]:
        result = await db.execute(
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

    async def get_by_id_with_relations(self, db: AsyncSession, appointment_id: int):
        result = await db.execute(
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

    async def get_by_id_with_slot(self, db: AsyncSession, appointment_id: int):
        result = await db.execute(
            select(Appointment)
            .options(selectinload(Appointment.slot))
            .where(Appointment.id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def cancel(
        self, db: AsyncSession, appointment: Appointment, cancel_reason: str
    ) -> Appointment:
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancel_reason = cancel_reason
        appointment.slot.status = ScheduleSlotStatus.AVAILABLE
        await db.commit()
        await db.refresh(appointment)
        return appointment


class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    def __init__(self):
        super().__init__(MedicalRecord)

    async def get_by_patient_id(
        self, db: AsyncSession, patient_id: int
    ) -> MedicalRecord | None:
        result = await db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient_id)
            .options(selectinload(MedicalRecord.patient).selectinload(Patient.user))
        )
        return result.scalar_one_or_none()

    async def get_by_record_number(
        self, db: AsyncSession, record_number: str
    ) -> MedicalRecord | None:
        result = await db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.record_number == record_number)
            .options(selectinload(MedicalRecord.patient).selectinload(Patient.user))
        )
        return result.scalar_one_or_none()

    async def exists_by_patient(self, db: AsyncSession, patient_id: int) -> bool:
        stmt = select(exists().where(MedicalRecord.patient_id == patient_id))
        result = await db.execute(stmt)
        return result.scalar_one()


class ExaminationRepository(BaseRepository[Examination]):
    def __init__(self):
        super().__init__(Examination)

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

    async def get_by_appointment(
        self, db: AsyncSession, appointment_id: int
    ) -> Examination | None:
        result = await db.execute(
            select(Examination)
            .where(Examination.appointment_id == appointment_id)
            .options(*self._examination_options())
        )
        return result.scalar_one_or_none()

    async def get_by_patient(
        self, db: AsyncSession, patient_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Examination]:
        result = await db.execute(
            select(Examination)
            .where(Examination.patient_id == patient_id)
            .offset(skip)
            .limit(limit)
            .options(*self._examination_options())
        )
        return list(result.scalars().all())

    async def get_by_doctor(
        self, db: AsyncSession, doctor_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Examination]:
        result = await db.execute(
            select(Examination)
            .where(Examination.doctor_id == doctor_id)
            .offset(skip)
            .limit(limit)
            .options(*self._examination_options())
        )
        return list(result.scalars().all())

    async def get_by_medical_record(
        self, db: AsyncSession, medical_record_id: int
    ) -> list[Examination]:
        result = await db.execute(
            select(Examination)
            .where(Examination.medical_record_id == medical_record_id)
            .options(*self._examination_options())
        )
        return list(result.scalars().all())


class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self):
        super().__init__(Prescription)

    @staticmethod
    def _prescription_options():
        return [
            selectinload(Prescription.examination),
            selectinload(Prescription.prescription_details).selectinload(
                PrescriptionDetail.medicine
            ),
        ]

    async def get_by_examination(
        self, db: AsyncSession, examination_id: int
    ) -> list[Prescription]:
        result = await db.execute(
            select(Prescription)
            .where(Prescription.examination_id == examination_id)
            .options(*self._prescription_options())
        )
        return list(result.scalars().all())


class PrescriptionDetailRepository(BaseRepository[PrescriptionDetail]):
    def __init__(self):
        super().__init__(PrescriptionDetail)

    async def get_by_prescription(
        self, db: AsyncSession, prescription_id: int
    ) -> list[PrescriptionDetail]:
        result = await db.execute(
            select(PrescriptionDetail)
            .where(PrescriptionDetail.prescription_id == prescription_id)
            .options(selectinload(PrescriptionDetail.medicine))
        )
        return list(result.scalars().all())

    async def get_by_medicine(
        self, db: AsyncSession, medicine_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[PrescriptionDetail]:
        result = await db.execute(
            select(PrescriptionDetail)
            .where(PrescriptionDetail.medicine_id == medicine_id)
            .offset(skip)
            .limit(limit)
            .options(selectinload(PrescriptionDetail.medicine))
        )
        return list(result.scalars().all())


class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self):
        super().__init__(Medicine)

    async def get_by_code(self, db: AsyncSession, code: str) -> Medicine | None:
        result = await db.execute(select(Medicine).where(Medicine.code == code))
        return result.scalar_one_or_none()

    async def get_active_medicines(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[Medicine]:
        result = await db.execute(
            select(Medicine)
            .where(Medicine.status == "active")
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_by_code(self, db: AsyncSession, code: str) -> Medicine | None:
        result = await db.execute(
            select(Medicine).where(Medicine.code == code, Medicine.status == "active")
        )
        return result.scalar_one_or_none()

    async def get_active_by_id(
        self, db: AsyncSession, medicine_id: int
    ) -> Medicine | None:
        result = await db.execute(
            select(Medicine).where(
                Medicine.id == medicine_id, Medicine.status == "active"
            )
        )
        return result.scalar_one_or_none()
