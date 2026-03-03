from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.db.session import get_db
from app.services.reports.kpi_calculator import KPICalculator  
from app.schemas.productivity import ProductivityKPI

router = APIRouter()

# Endpoint pour récupérer les KPIs de productivité pour une workstation donnée à une date spécifique
@router.get("/{workstation_id}/{report_date}", response_model=ProductivityKPI)
def get_kpi(workstation_id: int, report_date: date, db: Session = Depends(get_db)):
    return KPICalculator.get_workstation_kpi(workstation_id)