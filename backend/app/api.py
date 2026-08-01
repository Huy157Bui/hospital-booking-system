from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import (
    get_current_doctor,
    get_current_patient_profile,
    get_current_user,
    get_owned_schedule_slot,
)
from app.models import Patient, ScheduleSlot, User
from app.schemas import (
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
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        return auth_service.register(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", tags=["Authentication"], response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = auth_service.login(db, login_data.username, login_data.password)
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
def get_my_profile(current_user: User = Depends(get_current_user)):
    return user_service.get_profile(current_user)


appointment_service = AppointmentService()


@router.get(
    "/users/me/appointments", tags=["Appointments"], response_model=list[AppointmentOut]
)
async def get_my_appointments(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return appointment_service.get_user_appointments(db, current_user)


@router.post("/appointments", response_model=AppointmentOut, status_code=201)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    patient: Patient = Depends(get_current_patient_profile),
):
    return appointment_service.create_appointment(db, patient, appointment_data)


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment_detail(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return appointment_service.get_appointment_detail(db, appointment_id, current_user)


specialty_service = SpecialtyService()


@router.get("/specialties", tags=["Specialties"], response_model=list[SpecialtyOut])
def get_specialties(db: Session = Depends(get_db)):
    return specialty_service.get_specialties(db)


@router.get(
    "/specialties/{specialty_id}", tags=["Specialties"], response_model=SpecialtyOut
)
def get_specialty(specialty_id: int, db: Session = Depends(get_db)):
    try:
        return specialty_service.get_specialty(db, specialty_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


doctor_service = DoctorService()


@router.get("/doctors", tags=["Doctors"], response_model=list[DoctorOut])
def get_doctors(
    specialty_id: int | None = None, db: Session = Depends(get_db)
):  # query parameter
    return doctor_service.get_doctors(db, specialty_id)


@router.get("/doctors/{doctor_id}", tags=["Doctors"], response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    try:
        return doctor_service.get_doctor(db, doctor_id)
    except ValueError as e:
        if str(e) == "Doctor not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/doctors/{doctor_id}/schedule", response_model=DoctorScheduleOut, tags=["Doctors"]
)
def get_doctor_schedule(doctor_id: int, db: Session = Depends(get_db)):
    try:
        return doctor_service.get_doctor_schedule(db, doctor_id)
    except ValueError as e:
        if str(e) == "Doctor not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/doctors/me/schedule")
def get_my_schedule(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_doctor)
):
    return doctor_service.get_my_schedule(db, current_user)


@router.put("/doctors/me/schedules/{schedule_id}", response_model=ScheduleOut)
def update_my_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor),
):
    return doctor_service.update_my_schedule(
        db, current_doctor, schedule_id, schedule_data
    )


@router.patch("/doctors/me/schedule-slots/{slot_id}", response_model=ScheduleSlotOut)
def update_my_schedule_slot(
    slot_data: ScheduleSlotUpdate,
    db: Session = Depends(get_db),
    slot: ScheduleSlot = Depends(get_owned_schedule_slot),
):
    return doctor_service.update_my_schedule_slot(db, slot, slot_data)
