from fastapi import FastAPI
from app.database import engine, Base
from app.api import router

app = FastAPI()

@app.on_event("startup")
def init_db():
    Base.metadata.create_all(bind=engine)

app.include_router(router, prefix="/api/v1")