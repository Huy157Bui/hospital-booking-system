from datetime import date
from fastapi import APIRouter, Depends

from app.dependencies.commons import (
    get_current_user,
    get_current_patient_profile,
    get_appointment_record_access,
    get_current_doctor_profile,
    check_doctor,
    get_owned_schedule_slot,
)
from app.dependencies.services import (
    AIChatServiceDep,
    AppointmentServiceDep,
    AuthServiceDep,
    ChatSessionServiceDep,
    DoctorServiceDep,
    PatientServiceDep,
    PaymentServiceDep,
    SpecialtyServiceDep,
    UserServiceDep,
)
from app.models import Patient, ScheduleSlot, User, Doctor, Appointment
from app.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentOut,
    DoctorOut,
    DoctorScheduleOut,
    LoginRequest,
    ScheduleOut,
    ScheduleSlotOut,
    ScheduleSlotUpdate,
    ScheduleUpdate,
    SpecialtyOut,
    Token,
    UserCreate,
    UserOut,
    AppointmentStatusUpdate,
    ExaminationRecordCreate,
    ExaminationOut,
    PatientMedicalHistoryOut,
    PaymentOut,
    PaymentCreate,
    ChatResponse,
    ChatRequest,
    SendMessageRequest,
    SendMessageResponse,
    ChatMessageOut,
    ChatSessionOut,
    ChatSessionCreate,
    ChangePasswordRequest,
    UserUpdate,
    RefreshTokenRequest,
    TokenRefreshResponse,
    DoctorAvailabilityOut,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=UserOut, status_code=201)
async def register(user_data: UserCreate, auth_service: AuthServiceDep):
    return await auth_service.register(user_data)


@auth_router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, auth_service: AuthServiceDep):
    result = await auth_service.login(login_data.username, login_data.password)
    user_out = UserOut.model_validate(result["user"])
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        user=user_out,
    )

@auth_router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(data: RefreshTokenRequest, auth_service: AuthServiceDep):
    return await auth_service.refresh_access_token(data.refresh_token)


@auth_router.post("/logout")
async def logout(data: RefreshTokenRequest, auth_service: AuthServiceDep):
    await auth_service.logout(data.refresh_token)


@auth_router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    auth_service: AuthServiceDep,
    current_user: User = Depends(get_current_user),
):
    await auth_service.change_password(current_user, data.old_password, data.new_password)

users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.put("/me", response_model=UserOut)
async def update_my_profile(
    data: UserUpdate,
    user_service: UserServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await user_service.update_profile(current_user, data)

@users_router.get("/me", response_model=UserOut)
async def get_my_profile(
    user_service: UserServiceDep,
    current_user: User = Depends(get_current_user),
):
    return user_service.get_profile(current_user)


@users_router.get(
    "/me/medical-records",
    response_model=PatientMedicalHistoryOut
)
async def get_my_medical_records(
    patient_service: PatientServiceDep,
    patient: Patient = Depends(get_current_patient_profile),
):
    result = await patient_service.get_patient_medical_history(patient.id)
    return PatientMedicalHistoryOut(
        medical_record=result["medical_record"],
        examinations=result["examinations"],
    )

@users_router.get("/me/appointments", response_model=list[AppointmentOut])
async def get_my_appointments(
    appointment_service: AppointmentServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.get_user_appointments(current_user)

@users_router.get("/me/payments",response_model=list[PaymentOut])
async def get_my_payments(
    payment_service: PaymentServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await payment_service.get_user_payments(current_user)

@users_router.get(
    "/me/chat-sessions",
    response_model=list[ChatSessionOut]
)
async def get_my_chat_sessions(
    chat_session_service: ChatSessionServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await chat_session_service.get_user_sessions(current_user)


@users_router.put("/me", response_model=UserOut)
async def update_my_profile(
    data: UserUpdate,
    user_service: UserServiceDep,
    patient_service: PatientServiceDep,
    current_user: User = Depends(get_current_user),
):
    updated_user = await user_service.update_profile(current_user, data)

    return updated_user

appointments_router = APIRouter(prefix="/appointments", tags=["Appointments"])

@appointments_router.post("", response_model=AppointmentOut, status_code=201)

async def create_appointment(
    appointment_data: AppointmentCreate,
    appointment_service: AppointmentServiceDep,
    patient: Patient = Depends(get_current_patient_profile),
):
    return await appointment_service.create_appointment(
        patient,
        appointment_data,
    )

@appointments_router.get("/availability", response_model=DoctorAvailabilityOut)
async def get_doctor_availability(
    doctor_id: int,
    date: date,
    appointment_service: AppointmentServiceDep,
):
    return await appointment_service.get_doctor_availability(doctor_id, date)



@appointments_router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment_detail(
    appointment_id: int,
    appointment_service: AppointmentServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.get_accessible_appointment(
        appointment_id, current_user
    )


@appointments_router.patch("/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appointment_id: int,
    cancel_data: AppointmentCancel,
    appointment_service: AppointmentServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.cancel_appointment(
        appointment_id, current_user, cancel_data
    )

@appointments_router.patch("/{appointment_id}/status", response_model=AppointmentOut)
async def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    appointment_service: AppointmentServiceDep,
    doctor: Doctor = Depends(get_current_doctor_profile),
):
    return await appointment_service.update_appointment_status(
        appointment_id, status_update.status, doctor
    )


@appointments_router.post("/{appointment_id}/record", response_model=ExaminationOut)
async def add_examination_record(
    appointment_id: int,
    data: ExaminationRecordCreate,
    appointment_service: AppointmentServiceDep,
    doctor: Doctor = Depends(get_current_doctor_profile),
):
    return await appointment_service.add_examination_record(
        appointment_id, doctor, data
    )


@appointments_router.get("/{appointment_id}/record", response_model=ExaminationOut)
async def get_appointment_record(
    appointment_service: AppointmentServiceDep,
    appointment: Appointment = Depends(get_appointment_record_access),
):
    return await appointment_service.get_appointment_record(appointment)


@appointments_router.post(
    "/{appointment_id}/payment", response_model=PaymentOut, status_code=201
)
async def create_payment(
    appointment_id: int,
    appointment_service: AppointmentServiceDep,
    payment_data: PaymentCreate | None = None,
    current_user: User = Depends(get_current_user),
):
    payment_method = payment_data.payment_method if payment_data else None
    payment = await appointment_service.create_payment(
        appointment_id,
        current_user,
        payment_method,
    )
    return PaymentOut.model_validate(payment)


specialties_router = APIRouter(prefix="/specialties", tags=["Specialties"])

@specialties_router.get("", response_model=list[SpecialtyOut])
async def get_specialties(specialty_service: SpecialtyServiceDep):
    return await specialty_service.get_specialties()


@specialties_router.get("/{specialty_id}", response_model=SpecialtyOut)
async def get_specialty(specialty_id: int, specialty_service: SpecialtyServiceDep):
    return await specialty_service.get_specialty(specialty_id)


doctors_router = APIRouter(prefix="/doctors", tags=["Doctors"])


@doctors_router.get("", response_model=list[DoctorOut])
async def get_doctors(
    doctor_service: DoctorServiceDep,
    specialty_id: int | None = None,
):
    return await doctor_service.get_doctors(specialty_id)


@doctors_router.get("/{doctor_id}", response_model=DoctorOut)
async def get_doctor(doctor_id: int, doctor_service: DoctorServiceDep):

    return await doctor_service.get_doctor(doctor_id)


@doctors_router.get("/{doctor_id}/schedule", response_model=list[DoctorScheduleOut])
async def get_doctor_schedule(doctor_id: int, doctor_service: DoctorServiceDep):

    return await doctor_service.get_doctor_schedule(doctor_id)


@doctors_router.get("/me/schedule", response_model=list[ScheduleOut])
async def get_my_schedule(
    doctor_service: DoctorServiceDep,
    current_user: User = Depends(check_doctor),
):
    return await doctor_service.get_my_schedule(current_user)


@doctors_router.put("/me/schedules/{schedule_id}", response_model=ScheduleOut)
async def update_my_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    doctor_service: DoctorServiceDep,
    current_doctor: User = Depends(check_doctor),
):
    return await doctor_service.update_my_schedule(
        current_doctor, schedule_id, schedule_data
    )


@doctors_router.patch("/me/schedule-slots/{slot_id}", response_model=ScheduleSlotOut)
async def update_my_schedule_slot(
    slot_data: ScheduleSlotUpdate,
    doctor_service: DoctorServiceDep,
    slot: ScheduleSlot = Depends(get_owned_schedule_slot),
):
    return await doctor_service.update_my_schedule_slot(slot, slot_data)


patients_router = APIRouter(prefix="/patients", tags=["Patients"])


@patients_router.get(
    "/{patient_id}/medical-records", response_model=PatientMedicalHistoryOut
)
async def get_patient_medical_records(
    patient_id: int,
    patient_service: PatientServiceDep,
    current_user: User = Depends(get_current_user),
):
    result = await patient_service.get_patient_medical_history_with_access(
        patient_id, current_user
    )
    return PatientMedicalHistoryOut(
        medical_record=result["medical_record"],
        examinations=result["examinations"],
    )

payments_router = APIRouter(prefix="/payments", tags=["Payments"])

@payments_router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment_detail(
    payment_id: int,
    payment_service: PaymentServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await payment_service.get_payment_detail(payment_id, current_user)

chat_router = APIRouter(prefix="/chat", tags=["Chatbot AI"])

@chat_router.post("/ai", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    ai_chat_service: AIChatServiceDep,
):
    result = await ai_chat_service.chat(
        user_message=request.message,
        chat_history=request.chat_history
    )
    return ChatResponse(**result)

@chat_router.post("/sessions", response_model=ChatSessionOut, status_code=201)
async def create_chat_session(
    data: ChatSessionCreate,
    chat_session_service: ChatSessionServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await chat_session_service.create_session(current_user, data.title)

@chat_router.post(
    "/sessions/{session_id}/messages", response_model=SendMessageResponse, status_code=201
)
async def send_chat_message(
    session_id: int,
    data: SendMessageRequest,
    chat_session_service: ChatSessionServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await chat_session_service.send_message(
        session_id, current_user, data.content
    )


@chat_router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
async def get_chat_session_messages(
    session_id: int,
    chat_session_service: ChatSessionServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await chat_session_service.get_session_messages(session_id, current_user)


@chat_router.delete("/sessions/{session_id}", status_code=204)
async def delete_chat_session(
    session_id: int,
    chat_session_service: ChatSessionServiceDep,
    current_user: User = Depends(get_current_user),
):
    await chat_session_service.delete_session(session_id, current_user)