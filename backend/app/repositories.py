from typing import Generic, TypeVar, Type, Optional
from app.database import Base
from sqlalchemy.orm import Session
from app.models import User, Patient, Doctor, Specialty, Schedule, Medicine, Prescription, PrescriptionDetail, \
    Appointment, MedicalRecord, Examination
from datetime import date

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model):
        self.model = model

    def get_by_id(self, db: Session, id:int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
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

    def delete(self, db: Session, id: int) -> Optional[ModelType]:
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

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

class PatientRepository(BaseRepository[Patient]):
    def __init__(self):
        super().__init__(Patient)

    def get_by_identity_number(self, db: Session, identity: str) -> Optional[Patient]:
        return db.query(Patient).filter(Patient.identity_number == identity).first()

    def get_by_user_id(self, db: Session, user_id: int) -> Optional[Patient]:
        return db.query(Patient).filter(Patient.id == user_id).first()

class DoctorRepository(BaseRepository[Doctor]):
    def __init__(self):
        super().__init__(Doctor)

    def get_by_license(self, db: Session, license_number: str) -> Optional[Doctor]:
        return db.query(Doctor).filter(Doctor.license_number == license_number).first()

    def get_by_specialty(self, db: Session, specialty_id: int, *, skip: int = 0, limit: int = 100) -> list[Doctor]:
        return db.query(Doctor).filter(Doctor.specialty_id == specialty_id).offset(skip).limit(limit).all()

    def get_by_user_id(self, db: Session, user_id: int) -> Optional[Doctor]:
        return db.query(Doctor).filter(Doctor.id == user_id).first()

class SpecialtyRepository(BaseRepository[Specialty]):
    def __init__(self):
        super().__init__(Specialty)

    def get_by_name(self, db: Session, name:str) -> Optional[Specialty]:
        return db.query(Specialty).filter(Specialty.name == name).first()

class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self):
        super().__init__(Schedule)

    def get_by_doctor_and_date(self, db: Session, doctor_id: int, work_date: date) -> list[Schedule]:
        return db.query(Schedule).filter(Schedule.doctor_id == doctor_id,
                                              Schedule.work_date == work_date).all()

    def get_avaiable_schedules(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Schedule]:
        return db.query(Schedule).filter(Schedule.status == 'available').offset(skip).limit(limit).all()

class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self):
        super().__init__(Appointment)

    def get_by_patient(self, db: Session, patient_id: int, *, skip: int = 0, limit: int = 100) -> list[Appointment]:
        return db.query(Appointment).filter(Appointment.patient_id == patient_id).offset(skip).limit(limit).all()

    def get_by_doctor(self, db: Session, doctor_id: int, *, skip: int = 0, limit: int = 100) -> list[Appointment]:
        return db.query(Appointment).filter(Appointment.doctor_id == doctor_id).offset(skip).limit(limit).all()

class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    def __init__(self):
        super().__init__(MedicalRecord)

    def get_by_patient_id(self, db: Session, patient_id: int) -> Optional[MedicalRecord]:
        return db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).first()

    def get_by_record_number(self, db: Session, record_number: str) -> Optional[MedicalRecord]:
        return db.query(MedicalRecord).filter(MedicalRecord.record_number == record_number).first()

class ExaminationRepository(BaseRepository[Examination]):
    def __init__(self):
        super().__init__(Examination)

    def get_by_appointment(self, db: Session, appointment_id: int) -> Optional[Examination]:
        return db.query(Examination).filter(Examination.appointment_id == appointment_id).first()

    def get_by_patient(self, db: Session, patient_id: int, *, skip: int = 0, limit: int = 100) -> list[Examination]:
        return db.query(Examination).filter(Examination.patient_id == patient_id).offset(skip).limit(limit).all()

    def get_by_doctor(self, db: Session, doctor_id: int, *, skip: int = 0, limit: int = 100) -> list[Examination]:
        return db.query(Examination).filter(Examination.doctor_id == doctor_id).offset(skip).limit(limit).all()

class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self):
        super().__init__(Prescription)

    def get_by_examination(self, db: Session, examination_id: int) -> list[Prescription]:
        return db.query(Prescription).filter(Prescription.examination_id == examination_id).all()

class PrescriptionDetailRepository(BaseRepository[PrescriptionDetail]):
    def __init__(self):
        super().__init__(PrescriptionDetail)

    def get_by_prescription(self, db: Session, prescription_id: int) -> list[PrescriptionDetail]:
        return db.query(PrescriptionDetail).filter(PrescriptionDetail.prescription_id == prescription_id).all()

    def get_by_medicine(self, db: Session, medicine_id: int, *, skip: int = 0, limit: int = 100) -> list[PrescriptionDetail]:
        return db.query(PrescriptionDetail).filter(PrescriptionDetail.medicine_id == medicine_id).offset(skip).limit(limit).all()

class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self):
        super().__init__(Medicine)

    def get_by_code(self, db: Session, code: str) -> Optional[Medicine]:
        return db.query(Medicine).filter(Medicine.code == code).first()

    def get_active_medicines(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Medicine]:
        return db.query(Medicine).filter(Medicine.status == "active").offset(skip).limit(limit).all()