from sqlalchemy import Column, Integer, BigInteger, String, Enum, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.db.base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(BigInteger, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)

    alert_type = Column(String(50))
    severity = Column(Enum("LOW", "MEDIUM", "HIGH", name="alert_severity"))
    message = Column(String(255))

    is_resolved = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
