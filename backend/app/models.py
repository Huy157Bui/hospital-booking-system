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
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    avatar = Column(String(500), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.patient)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime, nullable=True)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)

    patient = relationship("Patient", back_populates="user", uselist=False)
    doctor = relationship("Doctor", back_populates="user", uselist=False)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(Enum(Gender), nullable=False, default=Gender.female)
    address = Column(String(500), nullable=True)
    identity_number = Column(String(50), nullable=True, unique=True)
    insurance_number = Column(String(50), nullable=True)
    blood_type = Column(String(10), nullable=True)
    emergency_contact = Column(String(50), nullable=True)
    occupation = Column(String(100), nullable=True)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)
    # 1-1
    user = relationship("User", back_populates="patient", uselist=False) # có khóa ngoại mặc định là false
    # 1-n
    appointments = relationship("Appointment", back_populates="patient", uselist=True)
    medical_record = relationship("MedicalRecord", back_populates="patient", uselist=False)
    examinations =relationship("Examination", back_populates="patient", uselist=True)

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=False)
    degree = Column(String(50), nullable=True)
    experience_year = Column(Integer, nullable=True)
    rate = Column(Float, nullable=True, default=0)
    consultation_fee = Column(Numeric(10,2), nullable=False, default=0)
    biography = Column(String(500), nullable=True)
    license_number = Column(String(50), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="active")
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)
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
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    location = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(50), nullable=True)
    working_hours = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)
    # 1-n
    doctors = relationship("Doctor", back_populates="specialty", uselist=True)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    work_date = Column(Date, nullable=False)
    start_date = Column(Time, nullable=False)
    end_date = Column(Time, nullable=False)
    max_patients = Column(Integer, nullable=False, default=10)
    status = Column(String(50), nullable=False, default="available")
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)
    # n-1
    doctor = relationship("Doctor", back_populates="schedules", uselist=False)

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    appointment_date = Column(DateTime, server_default=func.now(), nullable=False)
    reason = Column(String(500), nullable=True)
    note = Column(String(500), nullable=True)
    cancel_reason = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    # n-1
    patient = relationship("Patient", back_populates="appointments", uselist=False)
    doctor = relationship("Doctor", back_populates="appointments", uselist=False)
    schedule = relationship("Schedule")  # (hiện tại không có back_populates từ Schedule, dùng backref nếu cần)
    # 1-1
    examination = relationship("Examination", back_populates="appointment", uselist=False)

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True, nullable=False)
    record_number = Column(String(50), unique=True, nullable=False)
    allergy = Column(String(50), nullable=True)
    chronic_disease = Column(String(50), nullable=True)
    medical_history = Column(String(500), nullable=True)
    note = Column(String(500), nullable=True)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)
    # 1-1
    patient = relationship("Patient", back_populates="medical_record", uselist=False)
    # 1-n
    examinations = relationship("Examination", back_populates="medical_record", uselist=True)

class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), unique=True, nullable=False)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    symptom = Column(String(500), nullable=True)
    diagnosis = Column(String(500), nullable=True)
    conclusion = Column(String(500), nullable=True)
    disease_name = Column(String(200), nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    blood_pressure = Column(String(20), nullable=True)
    heart_rate = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    note = Column(String(500), nullable=True)
    examined_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="in_progress")
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)

    # 1-1
    appointment = relationship("Appointment", back_populates="examination", uselist=False)
    # n-1
    medical_record = relationship("MedicalRecord", back_populates="examinations", uselist=False)
    patient = relationship("Patient", back_populates="examinations", uselist=False)
    doctor = relationship("Doctor", back_populates="examinations", uselist=False)
    # 1-n
    prescriptions = relationship("Prescription", back_populates="examination", uselist=True)


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True)
    examination_id = Column(Integer, ForeignKey("examinations.id"), nullable=False)
    prescription_type = Column(SmallInteger, nullable=False)
    note = Column(String(500), nullable=True)
    total_amount = Column(Numeric(12,2), nullable=False, default=0)
    status = Column(SmallInteger, nullable=False, default=0)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)
    # n-1
    examination = relationship("Examination", back_populates="prescriptions", uselist=False)
    # 1-n
    prescription_details = relationship("PrescriptionDetail", back_populates="prescription", uselist=True)
    


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    unit = Column(String(50), nullable=False)
    dosage_form = Column(String(100), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    current_price = Column(Numeric(10, 2), nullable=False)
    description = Column(String(500), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active")
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, onupdate=func.now(), nullable=True)
    # 1-n
    prescription_details = relationship("PrescriptionDetail", back_populates="medicine",uselist=True)


class PrescriptionDetail(Base):
    __tablename__ = "prescription_detail"

    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(50), nullable=True)
    duration = Column(String(50), nullable=True)
    days = Column(Integer, nullable=True)
    instruction = Column(String(500), nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=False)
    # n-1
    prescription = relationship("Prescription", back_populates="prescription_details", uselist=False)
    medicine = relationship("Medicine", back_populates="prescription_details", uselist=False)