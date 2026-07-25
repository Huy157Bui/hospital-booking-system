from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.api import router
from app.admin import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(router)
app.include_router(admin_router)