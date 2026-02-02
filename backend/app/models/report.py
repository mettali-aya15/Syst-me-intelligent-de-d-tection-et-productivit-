from sqlalchemy import Column, Integer, BigInteger, ForeignKey, Date, DECIMAL
from app.db.base import Base

class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(BigInteger, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)

    report_date = Column(Date, nullable=False)
    working_time_seconds = Column(Integer, default=0)
    idle_time_seconds = Column(Integer, default=0)
    total_production = Column(Integer, default=0)
    efficiency = Column(DECIMAL(5, 2))
