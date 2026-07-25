from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserCreate, UserOut, Token, LoginRequest, UserResponse, AppointmentOut, SpecialtyOut
from app.services import AuthService, create_access_token, verify_password, hash_password, UserService, \
    AppointmentService, SpecialtyService
from app.models import User, UserRole
from jose import jwt, JWTError
from app.core import settings
from app.dependencies import get_current_user

router = APIRouter(prefix="")

auth_service = AuthService()

@router.post("/register", tags=["Authentication"], response_model=UserOut, status_code=201)
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
        return Token(access_token=result["access_token"], token_type=result["token_type"], user=user_out)
    except ValueError as e:
        if str(e) == "Invalid username or password":
            raise HTTPException(status_code=401,detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

user_service = UserService()

@router.get("/users/me", tags=["Users"], response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return user_service.get_profile(current_user)

appointment_service = AppointmentService()

@router.get("/users/me/appointments", tags=["Appointments"], response_model=list[AppointmentOut])
async def get_my_appointments(db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    return appointment_service.get_user_appointments(db, current_user)

specialty_service = SpecialtyService()

@router.get("/specialties", tags=["Specialties"], response_model=list[SpecialtyOut])
def get_specialties(db: Session = Depends(get_db)):
    return specialty_service.get_specialties(db)

@router.get("/specialties/{specialty_id}", tags=["Specialties"], response_model=SpecialtyOut)
def get_specialty(specialty_id: int, db: Session = Depends(get_db)):
    try:
        return specialty_service.get_specialty(db, specialty_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))