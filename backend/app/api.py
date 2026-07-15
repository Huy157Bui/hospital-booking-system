from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserCreate, UserOut, Token
from app.services import AuthService, create_access_token, verify_password, hash_password
from app.models import User
from jose import jwt
from app.core import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
    except:
        raise HTTPException(status_code=401)
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401)
    return user

# Auth endpoints
@router.post("/auth/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        user = service.register(data.username, data.password, data.role)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/auth/login", response_model=Token)
def login(username: str, password: str, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token}

# User endpoints (ví dụ)
@router.get("/users/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user