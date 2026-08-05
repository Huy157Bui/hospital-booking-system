from contextlib import asynccontextmanager
from urllib.request import Request

from fastapi import FastAPI
from starlette.responses import JSONResponse

from app.admin import router as admin_router
from app.routers import (
    router,
    patients_router,
    doctors_router,
    specialties_router,
    appointments_router,
    payments_router,
)
from app.exceptions import BaseException


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(BaseException)
async def app_exception_handler(request: Request, exc: BaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


app.include_router(router)
app.include_router(admin_router)
app.include_router(patients_router)
app.include_router(doctors_router)
app.include_router(specialties_router)
app.include_router(appointments_router)
app.include_router(payments_router)