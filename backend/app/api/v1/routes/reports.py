from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.db.session import get_db
from app.services.reports.daily_report import generate_daily_report
from app.schemas.report import DailyReport

router = APIRouter()

# Endpoint pour récupérer le rapport quotidien pour une date spécifique
@router.get("/{report_date}", response_model=DailyReport)
def get_daily_report(report_date: date, db: Session = Depends(get_db)):
    return generate_daily_report(db, report_date)