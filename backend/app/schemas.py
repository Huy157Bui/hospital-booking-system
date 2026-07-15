from pydantic import BaseModel
from typing import Optional
from app.models import UserRole

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.patient

class UserOut(BaseModel):
    id: int
    username: str
    role: UserRole
    active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"