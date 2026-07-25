from app.core import settings
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.models import User, UserRole, Appointment, Specialty
from app.repositories import UserRepository, AppointmentRepository, SpecialtyRepository
from app.schemas import UserCreate, SpecialtyCreate
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

class AuthService:
    def __init__(self):
        self.repo = UserRepository()

    def register(self, db: Session, user_data: UserCreate) -> User:
        if self.repo.get_by_username(db, user_data.username):
            raise ValueError("Username already exists")
        if self.repo.get_by_email(db, user_data.email):
            raise ValueError("Email already exists")

        hashed_password = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            phone=user_data.phone,
            avatar=user_data.avatar,
            role=user_data.role or UserRole.patient,
            is_active=True,
            password=hashed_password,
        )
        return self.repo.create(db, user)

    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        user = self.repo.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def login(self, db: Session, username: str, password: str) -> Optional[dict]:
        user = self.authenticate(db, username, password)
        if not user:
            return ValueError("Invalid username or password")
        if not user.is_active:
            raise ValueError("Account is inactive")

        user.last_login = datetime.utcnow()
        self.repo.update(db, user)

        access_token = create_access_token(data={"sub": user.username, "id": user.id, "role": user.role.value})
        return {"access_token": access_token, "token_type": "bearer", "user": user}

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        user = self.repo.get_by_username(db, username)
        if user is None:
            return None
        if not user.is_active:
            return None
        return user

class UserService:
    def __init__(self):
        self.repo = UserRepository()

    def get_profile(self, current_user: User):
        return current_user

class AppointmentService:
    def __init__(self):
        self.repo = AppointmentRepository()

    def get_user_appointments(self, db: Session, current_user: User) -> list[Appointment]:
        if current_user.role == UserRole.patient:
            return self.repo.get_by_patient(db, current_user.id)
        return self.repo.get_by_doctor(db, current_user.id)

class SpecialtyService:
    def __init__(self):
        self.repo = SpecialtyRepository()

    def get_specialties(self, db: Session) -> list[Specialty]:
        return self.repo.get_active_specialties(db)

    def get_specialty(self, db: Session, specialty_id: int) -> Specialty:
        specialty = self.repo.get_active_by_id(db, specialty_id)
        if specialty is None:
            raise ValueError("Specialty not found")
        return specialty

    def create_specialty(self,db: Session,specialty_data: SpecialtyCreate) -> Specialty:
        existed = self.repo.get_by_name(db, specialty_data.name)
        if existed:
            raise ValueError("Specialty already exists")
        specialty = Specialty(**specialty_data.model_dump())
        return self.repo.create(db, specialty)