from sqlalchemy import create_engine

from app.base import Base
from app.core import settings

sync_engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(bind=sync_engine)
print("✅ Đã tạo tất cả bảng thành công!")
