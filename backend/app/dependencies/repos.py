from typing import Annotated

from fastapi import Depends

from app.dependencies.db import DbDep
from app.repositories import (
    AppointmentRepository,
    DoctorRepository,
    ExaminationRepository,
    MedicalRecordRepository,
    MedicineRepository,
    PatientRepository,
    PaymentRepository,
    PrescriptionDetailRepository,
    PrescriptionRepository,
    ReportRepository,
    ScheduleRepository,
    ScheduleSlotRepository,
    SpecialtyRepository,
    UserRepository,
)


def get_appointment_repository(db: DbDep) -> AppointmentRepository:
    return AppointmentRepository(db)


AppointmentRepoDep = Annotated[
    AppointmentRepository, Depends(get_appointment_repository)
]


def get_schedule_repository(db: DbDep) -> ScheduleRepository:
    return ScheduleRepository(db)


ScheduleRepoDep = Annotated[
    ScheduleRepository, Depends(get_schedule_repository)
]


def get_doctor_repository(db: DbDep) -> DoctorRepository:
    return DoctorRepository(db)


DoctorRepoDep = Annotated[
    DoctorRepository, Depends(get_doctor_repository)
]


def get_user_repository(db: DbDep) -> UserRepository:
    return UserRepository(db)


UserRepoDep = Annotated[
    UserRepository, Depends(get_user_repository)
]


def get_patient_repository(db: DbDep) -> PatientRepository:
    return PatientRepository(db)


PatientRepoDep = Annotated[
    PatientRepository, Depends(get_patient_repository)
]


def get_schedule_slot_repository(db: DbDep) -> ScheduleSlotRepository:
    return ScheduleSlotRepository(db)


ScheduleSlotRepoDep = Annotated[
    ScheduleSlotRepository, Depends(get_schedule_slot_repository)
]


def get_medical_record_repository(db: DbDep) -> MedicalRecordRepository:
    return MedicalRecordRepository(db)


MedicalRecordRepoDep = Annotated[
    MedicalRecordRepository, Depends(get_medical_record_repository)
]


def get_examination_repository(db: DbDep) -> ExaminationRepository:
    return ExaminationRepository(db)


ExaminationRepoDep = Annotated[
    ExaminationRepository, Depends(get_examination_repository)
]


def get_prescription_repository(db: DbDep) -> PrescriptionRepository:
    return PrescriptionRepository(db)


PrescriptionRepoDep = Annotated[
    PrescriptionRepository, Depends(get_prescription_repository)
]


def get_prescription_detail_repository(db: DbDep) -> PrescriptionDetailRepository:
    return PrescriptionDetailRepository(db)


PrescriptionDetailRepoDep = Annotated[
    PrescriptionDetailRepository, Depends(get_prescription_detail_repository)
]


def get_medicine_repository(db: DbDep) -> MedicineRepository:
    return MedicineRepository(db)


MedicineRepoDep = Annotated[
    MedicineRepository, Depends(get_medicine_repository)
]


def get_specialty_repository(db: DbDep) -> SpecialtyRepository:
    return SpecialtyRepository(db)


SpecialtyRepoDep = Annotated[
    SpecialtyRepository, Depends(get_specialty_repository)
]


def get_payment_repository(db: DbDep) -> PaymentRepository:
    return PaymentRepository(db)


PaymentRepoDep = Annotated[
    PaymentRepository, Depends(get_payment_repository)
]


def get_report_repository(db: DbDep) -> ReportRepository:
    return ReportRepository(db)


ReportRepoDep = Annotated[
    ReportRepository, Depends(get_report_repository)
]