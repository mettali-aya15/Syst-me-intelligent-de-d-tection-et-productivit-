from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Workstation(Base):
    __tablename__ = "workstations"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)

    workstation_type = Column(String(100), nullable=False)
    # ✅ CORRIGÉ ICI : utiliser 'reference' au lieu de 'identifier'
    reference = Column(String(50), nullable=False)  # Pas 'identifier'
    zone = Column("location", String(50))  # Une seule ligne modifiée

    # ... reste du code inchangé ...

    # ✅ CORRIGÉ ICI : commenter la relation problématique
    # camera = relationship("Camera", back_populates="workstations")
    events = relationship("Event", back_populates="workstation")
    productions = relationship("ProductionCount", back_populates="workstation")