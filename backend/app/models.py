from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Enum,
                        ForeignKey, Float, Numeric, Time, Date, SmallInteger)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"

class Gender(str, enum.Enum):
    male = "male"
    female = "female"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(100))
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    avatar = Column(String(500))
    role = Column(Enum(UserRole), default=UserRole.patient)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, default=func.now())
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())

    patient = relationship("Patient", back_populates="user", uselist=False)
    doctor = relationship("Doctor", back_populates="user", uselist=False)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    date_of_birth = Column(DateTime)
    gender = Column(Enum(Gender), default=Gender.female)
    address = Column(String(500))
    identity_number = Column(String(50))
    insurance_number = Column(String(50))
    blood_type = Column(String(10))
    emergency_contact = Column(String(50))
    occupation = Column(String(100))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    # 1-1
    user = relationship("User", back_populates="patient", uselist=False) # có khóa ngoại mặc định là false
    # 1-n
    appointments = relationship("Appointment", back_populates="patient", uselist=True)
    medical_record = relationship("MedicalRecord", back_populates="patient", uselist=False)
    examinations =relationship("Examination", back_populates="patient", uselist=True)

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    specialty_id = Column(Integer, ForeignKey("specialties.id"))
    degree = Column(String(50))
    experience_year = Column(Integer)
    rate = Column(Float)
    consultation_fee = Column(Numeric(10,2))
    biography = Column(String(500))
    license_number = Column(String(50))
    status = Column(String(50))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    # 1-1
    user=relationship("User", back_populates="doctor", uselist=False)
    # n-1
    specialty = relationship("Specialty", back_populates="doctors", uselist=False)
    # 1-n
    schedules = relationship("Schedule", back_populates="doctor", uselist=True)
    appointments = relationship("Appointment", back_populates="doctor",uselist=True)
    examinations = relationship("Examination", back_populates="doctor", uselist=True)

class Specialty(Base):
    __tablename__ = "specialties"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(500))
    location = Column(String(500))
    phone = Column(String(50))
    email = Column(String(50))
    working_hours = Column(String(50))
    status = Column(String(50))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    # 1-n
    doctors = relationship("Doctor", back_populates="specialty", uselist=True)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    work_date = Column(Date)
    start_date = Column(Time)
    end_date = Column(Time)
    max_patients = Column(Integer)
    status = Column(String(50))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    # n-1
    doctor = relationship("Doctor", back_populates="schedules", uselist=False)

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    appointment_date = Column(DateTime, server_default=func.now())
    reason = Column(String(500))
    note = Column(String(500))
    cancel_reason = Column(String(500))
    status = Column(String(50))
    created_date = Column(DateTime, server_default=func.now())
    # n-1
    patient = relationship("Patient", back_populates="appointments", uselist=False)
    doctor = relationship("Doctor", back_populates="appointments", uselist=False)
    schedule = relationship("Schedule")  # (hiện tại không có back_populates từ Schedule, dùng backref nếu cần)
    # 1-1
    examination = relationship("Examination", back_populates="appointment", uselist=False)

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True)
    record_number = Column(String(50))
    allergy = Column(String(50))
    chronic_disease = Column(String(50))
    medical_history = Column(String(500))
    note = Column(String(500))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    # 1-1
    patient = relationship("Patient", back_populates="medical_record", uselist=False)
    # 1-n
    examinations = relationship("Examination", back_populates="medical_record", uselist=True)

class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), unique=True)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    symptom = Column(String(500))
    diagnosis = Column(String(500))
    conclusion = Column(String(500))
    disease_name = Column(String(200))
    height = Column(Float)
    weight = Column(Float)
    blood_pressure = Column(String(20))
    heart_rate = Column(Integer)
    temperature = Column(Float)
    note = Column(String(500))
    examined_at = Column(DateTime)
    status = Column(String(50))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())

    # 1-1
    appointment = relationship("Appointment", back_populates="examination", uselist=False)
    # n-1
    medical_record = relationship("MedicalRecord", back_populates="examinations", uselist=False)
    patient = relationship("Patient", back_populates="examinations", uselist=False)
    doctor = relationship("Doctor", back_populates="examinations", uselist=False)
    # 1-n
    prescriptions = relationship("PrescriptionDetail", back_populates="examination", uselist=True)


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True)
    examination_id = Column(Integer, ForeignKey("examinations.id"))
    prescription_type = Column(SmallInteger)
    note = Column(String(500))
    total_amount = Column(Numeric(12, 2))
    status = Column(SmallInteger)
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    # n-1
    examination = relationship("Examination", back_populates="prescriptions", uselist=False)
    # 1-n
    prescription_details = relationship("PrescriptionDetail", back_populates="prescription", uselist=True)
    


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    code = Column(String(50))
    unit = Column(String(50))
    dosage_form = Column(String(100))
    manufacturer = Column(String(200))
    current_price = Column(Numeric(10, 2))
    description = Column(String(500))
    stock_quantity = Column(Integer)
    status = Column(String(50))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    # 1-n
    prescription_details = relationship("PrescriptionDetail", back_populates="medicine",uselist=True)


class PrescriptionDetail(Base):
    __tablename__ = "prescription_detail"

    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    quantity = Column(Integer)
    unit_price = Column(Numeric(10, 2))
    dosage = Column(String(100))
    frequency = Column(String(50))
    duration = Column(String(50))
    days = Column(Integer)
    instruction = Column(String(500))
    subtotal = Column(Numeric(12, 2))
    # n-1
    prescription = relationship("Prescription", back_populates="prescription_details", uselist=False)
    medicine = relationship("Medicine", back_populates="prescription_details", uselist=False)

