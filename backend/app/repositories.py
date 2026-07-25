from typing import Generic, TypeVar, Type, Optional
from app.database import Base
from sqlalchemy.orm import Session
from app.models import User, Patient, Doctor, Specialty, Schedule, Medicine, Prescription, PrescriptionDetail, \
    Appointment, MedicalRecord, Examination
from datetime import date

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id:int) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, data: ModelType) -> ModelType:
        self.db.add(data)
        self.db.commit()
        self.db.refresh(data)
        return data

    def update(self, data: ModelType) -> ModelType:
        self.db.commit()
        self.db.refresh(data)
        return data

    def delete(self, id: int) -> Optional[ModelType]:
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj

    def count(self) -> int:
        return self.db.query(self.model).count()

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_active_users(self, *, skip: int = 0, limit: int = 100) -> list[User]:
        return self.db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

class PatientRepository(BaseRepository[Patient]):
    def __init__(self, db: Session):
        super().__init__(Patient, db)

    def get_by_identity_number(self, identity: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.identity_number == identity).first()

    def get_by_user_id(self, user_id: int) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.id == user_id).first()

class DoctorRepository(BaseRepository[Doctor]):
    def __init__(self, db: Session):
        super().__init__(Doctor, db)

    def get_by_license(self, license_number: str) -> Optional[Doctor]:
        return self.db.query(Doctor).filter(Doctor.license_number == license_number).first()

    def get_by_specialty(self, specialty_id: int, *, skip: int = 0, limit: int = 100) -> list[Doctor]:
        return self.db.query(Doctor).filter(Doctor.specialty_id == specialty_id).offset(skip).limit(limit).all()

    def get_by_user_id(self, user_id: int) -> Optional[Doctor]:
        return self.db.query(Doctor).filter(Doctor.id == user_id).first()

class SpecialtyRepository(BaseRepository[Specialty]):
    def __init__(self, db: Session):
        super().__init__(Specialty, db)

    def get_by_name(self, name:str) -> Optional[Specialty]:
        return self.db.query(Specialty).filter(Specialty.name == name).first()

class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self, db: Session):
        super().__init__(Schedule, db)

    def get_by_doctor_and_date(self, doctor_id: int, work_date: date) -> list[Schedule]:
        return self.db.query(Schedule).filter(Schedule.doctor_id == doctor_id,
                                              Schedule.work_date == work_date).all()

    def get_avaiable_schedules(self, *, skip: int = 0, limit: int = 100) -> list[Schedule]:
        return self.db.query(Schedule).filter(Schedule.status == 'available').offset(skip).limit(limit).all()

class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, db: Session):
        super().__init__(Appointment, db)

    def get_by_patient(self, patient_id: int, *, skip: int = 0, limit: int = 100) -> list[Appointment]:
        return self.db.query(Appointment).filter(Appointment.patient_id == patient_id).offset(skip).limit(limit).all()

    def get_by_doctor(self, doctor_id: int, *, skip: int = 0, limit: int = 100) -> list[Appointment]:
        return self.db.query(Appointment).filter(Appointment.doctor_id == doctor_id).offset(skip).limit(limit).all()

class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    def __init__(self, db: Session):
        super().__init__(MedicalRecord, db)

    def get_by_patient_id(self, patient_id: int) -> Optional[MedicalRecord]:
        return self.db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).first()

    def get_by_record_number(self, record_number: str) -> Optional[MedicalRecord]:
        return self.db.query(MedicalRecord).filter(MedicalRecord.record_number == record_number).first()

class ExaminationRepository(BaseRepository[Examination]):
    def __init__(self, db: Session):
        super().__init__(Examination, db)

    def get_by_appointment(self, appointment_id: int) -> Optional[Examination]:
        return self.db.query(Examination).filter(Examination.appointment_id == appointment_id).first()

    def get_by_patient(self, patient_id: int, *, skip: int = 0, limit: int = 100) -> list[Examination]:
        return self.db.query(Examination).filter(Examination.patient_id == patient_id).offset(skip).limit(limit).all()

    def get_by_doctor(self, doctor_id: int, *, skip: int = 0, limit: int = 100) -> list[Examination]:
        return self.db.query(Examination).filter(Examination.doctor_id == doctor_id).offset(skip).limit(limit).all()

class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self, db: Session):
        super().__init__(Prescription, db)

    def get_by_examination(self, examination_id: int) -> list[Prescription]:
        return self.db.query(Prescription).filter(Prescription.examination_id == examination_id).all()

class PrescriptionDetailRepository(BaseRepository[PrescriptionDetail]):
    def __init__(self, db: Session):
        super().__init__(PrescriptionDetail, db)

    def get_by_prescription(self, prescription_id: int) -> list[PrescriptionDetail]:
        return self.db.query(PrescriptionDetail).filter(PrescriptionDetail.prescription_id == prescription_id).all()

    def get_by_medicine(self, medicine_id: int, *, skip: int = 0, limit: int = 100) -> list[PrescriptionDetail]:
        return self.db.query(PrescriptionDetail).filter(PrescriptionDetail.medicine_id == medicine_id).offset(skip).limit(limit).all()

class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self, db: Session):
        super().__init__(Medicine, db)

    def get_by_code(self, code: str) -> Optional[Medicine]:
        return self.db.query(Medicine).filter(Medicine.code == code).first()

    def get_active_medicines(self, *, skip: int = 0, limit: int = 100) -> list[Medicine]:
        return self.db.query(Medicine).filter(Medicine.status == "active").offset(skip).limit(limit).all()