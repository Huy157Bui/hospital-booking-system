import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/hospitaldb"
    DATABASE_URL_ASYNC: str = "mysql+aiomysql://root:root@localhost:3306/hospitaldb"
    SECRET_KEY: str = "g1G7?O1tGYYF#J4G;Eg{sDoQfVeJdxoPGYCiFY${1xZ"
    SESSION_SECRET_KEY: str = "60a0ca472545b58f4bf93caa7b97c60b8eaf458de41c502a52bff890b9469f5f"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

settings = Settings()