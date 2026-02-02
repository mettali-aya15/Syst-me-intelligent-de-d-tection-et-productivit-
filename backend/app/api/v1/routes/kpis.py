from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.db.session import get_db
from app.services.reports.kpi_calculator import calculate_kpi
from app.schemas.productivity import ProductivityKPI

router = APIRouter()

# Endpoint pour récupérer les KPIs de productivité pour une machine donnée à une date spécifique
@router.get("/{machine_id}/{report_date}", response_model=ProductivityKPI)
def get_kpi(machine_id: int, report_date: date, db: Session = Depends(get_db)):
    return calculate_kpi(db, machine_id, report_date)
