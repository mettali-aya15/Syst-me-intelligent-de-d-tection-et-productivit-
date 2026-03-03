from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    name = Column(String(50), nullable=False)
    rtsp_url = Column(Text, nullable=False)
    zone = Column(String(50))
    is_active = Column(Boolean, default=True)

    workstations = relationship("Workstation", back_populates="camera")