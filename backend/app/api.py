from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserCreate, UserOut, Token, LoginRequest, UserResponse, AppointmentOut
from app.services import AuthService, create_access_token, verify_password, hash_password, UserService, AppointmentService
from app.models import User
from jose import jwt, JWTError
from app.core import settings

router = APIRouter(prefix="", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
auth_service = AuthService()

async def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        raise credentials_exception
    username = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = auth_service.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):

    try:
        user = auth_service.register(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    result = auth_service.login(db, login_data.username, login_data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_out = UserOut.model_validate(result["user"])
    return Token(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user=user_out
    )

user_service = UserService()

@router.get("/users/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return user_service.get_profile(current_user)

appointment_service = AppointmentService()

@router.get("/users/me/appointments", response_model=list[AppointmentOut])
async def get_my_appointments(db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    return appointment_service.get_user_appointments(db, current_user)

