from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    role = Column(Enum("ADMIN", "SUPERVISOR", "VIEWER", name="user_role"))
    created_at = Column(TIMESTAMP, server_default=func.now())
