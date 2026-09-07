import logging
from contextlib import asynccontextmanager
from starlette.requests import Request
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.admin import admin_router, reports_router
from app.routers import (
    auth_router,
    users_router,
    patients_router,
    doctors_router,
    specialties_router,
    appointments_router,
    payments_router,
    chat_router,
    medicines_router,
)
from app.exceptions import AppException
from app.core import settings
from app.admin_ui import setup_admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    https_only=False,
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(patients_router)
app.include_router(doctors_router)
app.include_router(specialties_router)
app.include_router(appointments_router)
app.include_router(payments_router)
app.include_router(chat_router)
app.include_router(reports_router)
app.include_router(medicines_router)

setup_admin(app)