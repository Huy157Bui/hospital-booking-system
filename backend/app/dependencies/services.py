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
    AIChatService,
    AppointmentService,
    AuthService,
    DoctorSearchService,
    DoctorService,
    EmergencyService,
    LLMService,
    PatientService,
    PaymentService,
    RAGService,
    ReportService,
    ScheduleService,
    SpecialtyDetectionService,
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


def get_auth_service(user_repo: UserRepoDep) -> AuthService:
    return AuthService(user_repo=user_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(user_repo: UserRepoDep) -> UserService:
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


def get_report_service(
    payment_repo: PaymentRepoDep, report_repo: ReportRepoDep
) -> ReportService:
    return ReportService(payment_repo=payment_repo, report_repo=report_repo)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


def get_specialty_detection_service() -> SpecialtyDetectionService:
    return SpecialtyDetectionService()


SpecialtyDetectionServiceDep = Annotated[
    SpecialtyDetectionService, Depends(get_specialty_detection_service)
]


def get_rag_service() -> RAGService:
    return RAGService()


RAGServiceDep = Annotated[RAGService, Depends(get_rag_service)]


def get_emergency_service() -> EmergencyService:
    return EmergencyService()


EmergencyServiceDep = Annotated[EmergencyService, Depends(get_emergency_service)]


def get_llm_service() -> LLMService:
    return LLMService()


LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]


def get_doctor_search_service(
    doctor_repo: DoctorRepoDep,
) -> DoctorSearchService:
    return DoctorSearchService(doctor_repo=doctor_repo)


DoctorSearchServiceDep = Annotated[
    DoctorSearchService, Depends(get_doctor_search_service)
]


def get_ai_chat_service(
    specialty_detector: SpecialtyDetectionServiceDep,
    doctor_search: DoctorSearchServiceDep,
    rag_service: RAGServiceDep,
    emergency_service: EmergencyServiceDep,
    llm_service: LLMServiceDep,
) -> AIChatService:
    return AIChatService(
        specialty_detector=specialty_detector,
        doctor_search=doctor_search,
        rag_service=rag_service,
        emergency_service=emergency_service,
        llm_service=llm_service,
    )


AIChatServiceDep = Annotated[AIChatService, Depends(get_ai_chat_service)]