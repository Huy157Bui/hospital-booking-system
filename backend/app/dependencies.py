from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from jose import jwt, JWTError
from app.core import settings
from app.models import User, UserRole
from app.services import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth_service = AuthService()

async def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials",
                                          headers={"WWW-Authenticate": "Bearer"},)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise credentials_exception
    user_id = payload.get("id")
    if user_id is None:
        raise credentials_exception
    user = auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=403,detail="Inactive user")
    return current_user

def get_current_patient(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403,detail="Only patient can access this resource")
    return current_user

def get_current_doctor(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403,detail="Only doctor can access this resource")
    return current_user

def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admin can access this resource")
    return current_user

