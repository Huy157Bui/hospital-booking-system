from app.repositories import UserRepository
from app.core import settings
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

class AuthService:
    def __init__(self, db):
        self.repo = UserRepository(db)

    def register(self, username: str, password: str, role: str = "candidate"):
        if self.repo.get_by_username(username):
            raise ValueError("Username already exists")
        hashed = hash_password(password)
        user = self.repo.create(username, hashed, role)
        return user

    def authenticate(self, username: str, password: str):
        user = self.repo.get_by_username(username)
        if not user or not verify_password(password, user.password):
            return None
        return user