from datetime import date
from typing import Generic, TypeVar

from sqlalchemy.orm import Session, joinedload

from app.database import Base
from app.models import (
    Appointment,
    Doctor,
    Examination,
    MedicalRecord,
    Medicine,
    Patient,
    Prescription,
    PrescriptionDetail,
    Schedule,
    ScheduleSlot,
    ScheduleStatus,
    Specialty,
    User,
)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model):
        self.model = model

    def get_by_id(self, db: Session, id: int) -> ModelType | None:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, data: ModelType) -> ModelType:
        db.add(data)
        db.commit()
        db.refresh(data)
        return data

    def update(self, db: Session, data: ModelType) -> ModelType:
        db.commit()
        db.refresh(data)
        return data

    def delete(self, db: Session, id: int) -> ModelType | None:
        obj = self.get_by_id(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def count(self, db: Session) -> int:
        return db.query(self.model).count()


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def get_active_users(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[User]:
        return (
            db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )


class PatientRepository(BaseRepository[Patient]):
    def __init__(self):
        super().__init__(Patient)

    def get_by_identity_number(self, db: Session, identity: str) -> Patient | None:
        return db.query(Patient).filter(Patient.identity_number == identity).first()

    def get_by_user_id(self, db: Session, user_id: int):
        return db.query(Patient).filter(Patient.id == user_id).first()


class DoctorRepository(BaseRepository[Doctor]):
    def __init__(self):
        super().__init__(Doctor)

    def get_by_license(self, db: Session, license_number: str) -> Doctor | None:
        return db.query(Doctor).filter(Doctor.license_number == license_number).first()

    def get_by_specialty(
        self, db: Session, specialty_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Doctor]:
        return (
            db.query(Doctor)
            .filter(Doctor.specialty_id == specialty_id, Doctor.status == "active")
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_doctors(self, db: Session) -> list[Doctor]:
        return db.query(Doctor).filter(Doctor.status == "active").all()

    def get_active_doctors_by_specialty(
        self, db: Session, specialty_id: int
    ) -> list[Doctor]:
        return (
            db.query(Doctor)
            .filter(Doctor.status == "active", Doctor.specialty_id == specialty_id)
            .all()
        )

    def get_active_by_id(self, db: Session, doctor_id: int) -> Doctor | None:
        return (
            db.query(Doctor)
            .filter(Doctor.id == doctor_id, Doctor.status == "active")
            .first()
        )

    def get_by_user_id(self, db: Session, user_id: int) -> Doctor | None:
        return db.query(Doctor).filter(Doctor.id == user_id).first()

    def count_active_by_specialty(self, db: Session, specialty_id: int) -> int:
        return (
            db.query(Doctor)
            .filter(Doctor.specialty_id == specialty_id, Doctor.status == "active")
            .count()
        )

    def exists_active_by_specialty(self, db: Session, specialty_id: int) -> bool:
        return (
            db.query(Doctor)
            .filter(Doctor.specialty_id == specialty_id, Doctor.status == "active")
            .first()
            is not None
        )


class SpecialtyRepository(BaseRepository[Specialty]):
    def __init__(self):
        super().__init__(Specialty)

    def get_by_name(self, db: Session, name: str) -> Specialty | None:
        return db.query(Specialty).filter(Specialty.name == name).first()

    def get_active_specialties(self, db: Session) -> list[Specialty]:
        return (
            db.query(Specialty)
            .filter(Specialty.status == "active")
            .order_by(Specialty.name)
            .all()
        )

    def get_active_by_id(self, db: Session, specialty_id: int) -> Specialty | None:
        return (
            db.query(Specialty)
            .filter(Specialty.id == specialty_id, Specialty.status == "active")
            .first()
        )

    def toggle_status(self, db: Session, specialty: Specialty) -> Specialty:
        if specialty.status == "active":
            specialty.status = "inactive"
        else:
            specialty.status = "active"
        return self.update(db, specialty)


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self):
        super().__init__(Schedule)

    def get_by_doctor(self, db: Session, doctor_id: int):
        return db.query(Schedule).filter(Schedule.doctor_id == doctor_id).all()

    def get_by_doctor_and_date(
        self, db: Session, doctor_id: int, work_date: date
    ) -> list[Schedule]:
        return (
            db.query(Schedule)
            .filter(Schedule.doctor_id == doctor_id, Schedule.work_date == work_date)
            .all()
        )

    def get_open_schedules(self, db: Session, *, skip: int = 0, limit: int = 100):
        return (
            db.query(Schedule)
            .filter(Schedule.status == ScheduleStatus.OPEN)
            .offset(skip)
            .limit(limit)
            .all()
        )


class ScheduleSlotRepository(BaseRepository[ScheduleSlot]):
    def __init__(self):
        super().__init__(ScheduleSlot)

    def get_by_schedule(
        self,
        db: Session,
        schedule_id: int,
    ) -> list[ScheduleSlot]:
        return (
            db.query(ScheduleSlot).filter(ScheduleSlot.schedule_id == schedule_id).all()
        )


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self):
        super().__init__(Appointment)

    def get_by_patient(
        self, db: Session, patient_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Appointment]:
        return (
            db.query(Appointment)
            .filter(Appointment.patient_id == patient_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_doctor(
        self, db: Session, doctor_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Appointment]:
        return (
            db.query(Appointment)
            .join(Appointment.slot)
            .join(ScheduleSlot.schedule)
            .filter(Schedule.doctor_id == doctor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_with_relations(self, db: Session, appointment_id: int):
        return (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient).joinedload(Patient.user),
                joinedload(Appointment.slot)
                .joinedload(ScheduleSlot.schedule)
                .joinedload(Schedule.doctor)
                .joinedload(Doctor.user),
            )
            .filter(Appointment.id == appointment_id)
            .first()
        )


class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    def __init__(self):
        super().__init__(MedicalRecord)

    def get_by_patient_id(self, db: Session, patient_id: int) -> MedicalRecord | None:
        return (
            db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == patient_id)
            .first()
        )

    def get_by_record_number(
        self, db: Session, record_number: str
    ) -> MedicalRecord | None:
        return (
            db.query(MedicalRecord)
            .filter(MedicalRecord.record_number == record_number)
            .first()
        )

    def exists_by_patient(self, db: Session, patient_id: int) -> bool:
        return (
            db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == patient_id)
            .first()
            is not None
        )


class ExaminationRepository(BaseRepository[Examination]):
    def __init__(self):
        super().__init__(Examination)

    def get_by_appointment(
        self, db: Session, appointment_id: int
    ) -> Examination | None:
        return (
            db.query(Examination)
            .filter(Examination.appointment_id == appointment_id)
            .first()
        )

    def get_by_patient(
        self, db: Session, patient_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Examination]:
        return (
            db.query(Examination)
            .filter(Examination.patient_id == patient_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_doctor(
        self, db: Session, doctor_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Examination]:
        return (
            db.query(Examination)
            .filter(Examination.doctor_id == doctor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_medical_record(self, db: Session, medical_record_id: int):
        return (
            db.query(Examination)
            .filter(Examination.medical_record_id == medical_record_id)
            .all()
        )


class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self):
        super().__init__(Prescription)

    def get_by_examination(
        self, db: Session, examination_id: int
    ) -> list[Prescription]:
        return (
            db.query(Prescription)
            .filter(Prescription.examination_id == examination_id)
            .all()
        )


class PrescriptionDetailRepository(BaseRepository[PrescriptionDetail]):
    def __init__(self):
        super().__init__(PrescriptionDetail)

    def get_by_prescription(
        self, db: Session, prescription_id: int
    ) -> list[PrescriptionDetail]:
        return (
            db.query(PrescriptionDetail)
            .filter(PrescriptionDetail.prescription_id == prescription_id)
            .all()
        )

    def get_by_medicine(
        self, db: Session, medicine_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[PrescriptionDetail]:
        return (
            db.query(PrescriptionDetail)
            .filter(PrescriptionDetail.medicine_id == medicine_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self):
        super().__init__(Medicine)

    def get_by_code(self, db: Session, code: str) -> Medicine | None:
        return db.query(Medicine).filter(Medicine.code == code).first()

    def get_active_medicines(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[Medicine]:
        return (
            db.query(Medicine)
            .filter(Medicine.status == "active")
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_by_code(self, db: Session, code: str):
        return (
            db.query(Medicine)
            .filter(Medicine.code == code, Medicine.status == "active")
            .first()
        )

    def get_active_by_id(self, db: Session, medicine_id: int):
        return (
            db.query(Medicine)
            .filter(Medicine.id == medicine_id, Medicine.status == "active")
            .first()
        )
