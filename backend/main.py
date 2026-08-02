from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.admin import router as admin_router
from app.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router)
app.include_router(admin_router)
