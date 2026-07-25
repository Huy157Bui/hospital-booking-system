from app.repositories import UserRepository
from app.core import settings
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.models import User, UserRole
from app.repositories import UserRepository
from app.schemas import UserCreate

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
    def __init__(self, db):
        self.repo = UserRepository(db)

    def register(self, user_data: UserCreate) -> User:
        if self.repo.get_by_username(user_data.username):
            raise ValueError("Username already exists")
        if self.repo.get_by_email(user_data.email):
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
        return self.repo.create(user)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.repo.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def login(self, username: str, password: str) -> Optional[dict]:
        user = self.authenticate(username, password)
        if not user:
            return None
        if not user.is_active:
            raise ValueError("Account is inactive")

        # Cập nhật last_login
        user.last_login = datetime.utcnow()
        self.repo.update(user)

        # Tạo JWT token
        access_token = create_access_token(
            data={"sub": user.username, "id": user.id, "role": user.role.value}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }