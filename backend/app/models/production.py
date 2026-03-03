from sqlalchemy import Column, Integer, BigInteger, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

# Dans app/models/production.py
class ProductionCount(Base):
    __tablename__ = "production_counts"

    id = Column(Integer, primary_key=True, index=True)
    workstation_id = Column(Integer, ForeignKey("workstations.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    recorded_at = Column(TIMESTAMP, server_default=func.now())

    # ✅ CORRIGÉ ICI : utiliser 'reference' au lieu de 'identifier'
    workstation = relationship("Workstation", back_populates="productions")