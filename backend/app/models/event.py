from sqlalchemy import Column, Integer, BigInteger, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(BigInteger, primary_key=True, index=True)
    workstation_id = Column(Integer, ForeignKey("workstations.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    event_type = Column(
        Enum(
            "EMPLOYEE_STARTED_WORK",
            "EMPLOYEE_STOPPED_WORK",
            "EMPLOYEE_ABSENT",
            "WORKSTATION_ACTIVE",
            "WORKSTATION_IDLE",
            "PRODUCTION",
            "ANOMALY",
            name="event_type"
        ),
        nullable=False
    )

    duration_seconds = Column(Integer, default=0)
    event_time = Column(TIMESTAMP, server_default=func.now())

    workstation = relationship("Workstation", back_populates="events")