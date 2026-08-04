import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/hospitaldb"
    DATABASE_URL_ASYNC: str = "mysql+aiomysql://root:root@localhost:3306/hospitaldb"
    SECRET_KEY: str = "g1G7?O1tGYYF#J4G;Eg{sDoQfVeJdxoPGYCiFY${1xZ"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()