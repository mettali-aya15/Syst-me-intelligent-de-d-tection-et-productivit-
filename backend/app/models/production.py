from sqlalchemy import Column, Integer, BigInteger, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProductionCount(Base):
    __tablename__ = "production_counts"

    id = Column(BigInteger, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    recorded_at = Column(TIMESTAMP, server_default=func.now())

    machine = relationship("Machine", back_populates="productions")
