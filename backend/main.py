from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.admin import router as admin_router
from app.routers import (
    router,
    patients_router,
    doctors_router,
    specialties_router,
    appointments_router,
    payments_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(router)
app.include_router(admin_router)
app.include_router(patients_router)
app.include_router(doctors_router)
app.include_router(specialties_router)
app.include_router(appointments_router)
app.include_router(payments_router)
