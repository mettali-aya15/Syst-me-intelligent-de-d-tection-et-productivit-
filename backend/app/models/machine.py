from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)

    machine_type = Column(Enum("SEWING", "KNITTING", name="machine_type"), nullable=False)
    reference = Column(String(50), nullable=False)
    location = Column(String(50))

    camera = relationship("Camera", back_populates="machines")
    events = relationship("Event", back_populates="machine")
    productions = relationship("ProductionCount", back_populates="machine")
    