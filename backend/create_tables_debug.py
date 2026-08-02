from sqlalchemy import create_engine
from app.base import Base
from app.core import settings

print(">>> Importing app.models ...")
try:
    import app.models

    print(">>> Import successful.")
except Exception as e:
    print(f"!!! ERROR importing models: {e}")
    raise

print(">>> Tables in metadata:", list(Base.metadata.tables.keys()))

sync_engine = create_engine(settings.DATABASE_URL, echo=True)  # echo=True để xem SQL
print(">>> Creating tables...")
Base.metadata.create_all(bind=sync_engine)
print(">>> Done.")