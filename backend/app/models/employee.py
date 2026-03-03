from sqlalchemy import Column, Integer, String, Boolean
from app.db.base import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True)
    role = Column(String(50))
    is_active = Column(Boolean, default=True)