from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    get_current_doctor,
    get_current_patient_profile,
    get_current_user,
    get_owned_schedule_slot,
    get_current_doctor_profile,
)
from app.models import Patient, ScheduleSlot, User, Doctor
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
)
from app.services import (
    AppointmentService,
    AuthService,
    DoctorService,
    SpecialtyService,
    UserService,
)

router = APIRouter(prefix="")

auth_service = AuthService()


@router.post(
    "/register", tags=["Authentication"], response_model=UserOut, status_code=201
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.register(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", tags=["Authentication"], response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await auth_service.login(db, login_data.username, login_data.password)
        user_out = UserOut.model_validate(result["user"])
        return Token(
            access_token=result["access_token"],
            token_type=result["token_type"],
            user=user_out,
        )
    except ValueError as e:
        if str(e) == "Invalid username or password":
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


user_service = UserService()


@router.get("/users/me", tags=["Users"], response_model=UserOut)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return user_service.get_profile(current_user)


appointment_service = AppointmentService()


@router.get(
    "/users/me/appointments", tags=["Appointments"], response_model=list[AppointmentOut]
)
async def get_my_appointments(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return await appointment_service.get_user_appointments(db, current_user)


@router.post("/appointments", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    patient: Patient = Depends(get_current_patient_profile),
):
    return await appointment_service.create_appointment(db, patient, appointment_data)


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
async def get_appointment_detail(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.get_appointment_detail(
        db, appointment_id, current_user
    )


@router.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appointment_id: int,
    cancel_data: AppointmentCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.cancel_appointment(
        db, appointment_id, current_user, cancel_data
    )

@router.patch('/appointments/{appointment_id}/status', response_model=AppointmentOut)
async def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    return await appointment_service.update_appointment_status(db, appointment_id, status_update.status, doctor)

@router.post("/appointments/{appointment_id}/record", response_model=ExaminationOut)
async def add_examination_record(
    appointment_id: int,
    data: ExaminationRecordCreate = ...,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile()),
    service: AppointmentService = Depends(),
):
    exam = await service.add_examination_record(db, appointment_id, doctor, data)
    return exam


specialty_service = SpecialtyService()

@router.get("/specialties", tags=["Specialties"], response_model=list[SpecialtyOut])
async def get_specialties(db: AsyncSession = Depends(get_db)):
    return await specialty_service.get_specialties(db)


@router.get(
    "/specialties/{specialty_id}", tags=["Specialties"], response_model=SpecialtyOut
)
async def get_specialty(specialty_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await specialty_service.get_specialty(db, specialty_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


doctor_service = DoctorService()


@router.get("/doctors", tags=["Doctors"], response_model=list[DoctorOut])
async def get_doctors(
    specialty_id: int | None = None, db: AsyncSession = Depends(get_db)
):
    return await doctor_service.get_doctors(db, specialty_id)


@router.get("/doctors/{doctor_id}", tags=["Doctors"], response_model=DoctorOut)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await doctor_service.get_doctor(db, doctor_id)
    except ValueError as e:
        if str(e) == "Doctor not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/doctors/{doctor_id}/schedule", response_model=DoctorScheduleOut, tags=["Doctors"]
)
async def get_doctor_schedule(doctor_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await doctor_service.get_doctor_schedule(db, doctor_id)
    except ValueError as e:
        if str(e) == "Doctor not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/doctors/me/schedule")
async def get_my_schedule(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_doctor)
):
    return await doctor_service.get_my_schedule(db, current_user)


@router.put("/doctors/me/schedules/{schedule_id}", response_model=ScheduleOut)
async def update_my_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor),
):
    return await doctor_service.update_my_schedule(
        db, current_doctor, schedule_id, schedule_data
    )


@router.patch("/doctors/me/schedule-slots/{slot_id}", response_model=ScheduleSlotOut)
async def update_my_schedule_slot(
    slot_data: ScheduleSlotUpdate,
    db: AsyncSession = Depends(get_db),
    slot: ScheduleSlot = Depends(get_owned_schedule_slot),
):
    return await doctor_service.update_my_schedule_slot(db, slot, slot_data)
