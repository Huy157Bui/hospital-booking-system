from typing import Annotated

from fastapi import Depends


from app.dependencies.repos import (
    AppointmentRepoDep,
    DoctorRepoDep,
    ExaminationRepoDep,
    MedicalRecordRepoDep,
    MedicineRepoDep,
    PatientRepoDep,
    PaymentRepoDep,
    PrescriptionDetailRepoDep,
    PrescriptionRepoDep,
    ReportRepoDep,
    ScheduleRepoDep,
    ScheduleSlotRepoDep,
    SpecialtyRepoDep,
    UserRepoDep,
)

from app.services import (
    AppointmentService,
    AuthService,
    DoctorService,
    PatientService,
    PaymentService,
    ReportService,
    ScheduleService,
    SpecialtyService,
    UserService,
)


def get_appointment_service(
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
) -> AppointmentService:
    return AppointmentService(
        appointment_repo=appointment_repo,
        slot_repo=slot_repo,
        doctor_repo=doctor_repo,
        patient_repo=patient_repo,
        medical_record_repo=medical_record_repo,
        examination_repo=examination_repo,
        prescription_repo=prescription_repo,
        prescription_detail_repo=prescription_detail_repo,
        medicine_repo=medicine_repo,
        payment_repo=payment_repo,
    )


AppointmentServiceDep = Annotated[
    AppointmentService,
    Depends(get_appointment_service),
]


def get_auth_service(
    user_repo: UserRepoDep,
) -> AuthService:
    return AuthService(user_repo=user_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(
    user_repo: UserRepoDep,
) -> UserService:
    return UserService(user_repo=user_repo)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_specialty_service(
    specialty_repo: SpecialtyRepoDep,
    doctor_repo: DoctorRepoDep,
) -> SpecialtyService:
    return SpecialtyService(
        specialty_repo=specialty_repo,
        doctor_repo=doctor_repo,
    )


SpecialtyServiceDep = Annotated[SpecialtyService, Depends(get_specialty_service)]


def get_doctor_service(
    doctor_repo: DoctorRepoDep,
    user_repo: UserRepoDep,
    specialty_repo: SpecialtyRepoDep,
    schedule_repo: ScheduleRepoDep,
    appointment_repo: AppointmentRepoDep,
    slot_repo: ScheduleSlotRepoDep,
) -> DoctorService:
    return DoctorService(
        doctor_repo=doctor_repo,
        user_repo=user_repo,
        specialty_repo=specialty_repo,
        schedule_repo=schedule_repo,
        appointment_repo=appointment_repo,
        slot_repo=slot_repo,
    )


DoctorServiceDep = Annotated[DoctorService, Depends(get_doctor_service)]


def get_patient_service(
    patient_repo: PatientRepoDep,
    medical_record_repo: MedicalRecordRepoDep,
    examination_repo: ExaminationRepoDep,
    doctor_repo: DoctorRepoDep,
    appointment_repo: AppointmentRepoDep,
) -> PatientService:
    return PatientService(
        patient_repo=patient_repo,
        medical_record_repo=medical_record_repo,
        examination_repo=examination_repo,
        doctor_repo=doctor_repo,
        appointment_repo=appointment_repo,
    )


PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]


def get_schedule_service(
    schedule_repo: ScheduleRepoDep,
    slot_repo: ScheduleSlotRepoDep,
) -> ScheduleService:
    return ScheduleService(
        schedule_repo=schedule_repo,
        slot_repo=slot_repo,
    )


ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]


def get_payment_service(payment_repo: PaymentRepoDep) -> PaymentService:
    return PaymentService(payment_repo=payment_repo)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]


async def get_report_service(
    payment_repo: PaymentRepoDep, report_repo: ReportRepoDep
) -> ReportService:
    return ReportService(payment_repo=payment_repo, report_repo=report_repo)

ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
