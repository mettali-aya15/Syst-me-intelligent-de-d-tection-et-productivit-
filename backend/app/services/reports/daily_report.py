from sqlalchemy.orm import Session
from datetime import date
from typing import List
from app.models.machine import Machine
from app.services.reports.kpi_calculator import calculate_kpi
from app.schemas.report import DailyReport, MachineReport

def generate_daily_report(db: Session, report_date: date) -> DailyReport:
    machines: List[Machine] = db.query(Machine).all()
    machine_reports: List[MachineReport] = []

    total_prod = 0
    total_expected = 0

    for m in machines:
        kpi = calculate_kpi(db, m.id, report_date)
        machine_reports.append(
            MachineReport(
                machine_name=m.reference,
                total_output=kpi.total_cycles,
                productivity_rate=kpi.productivity_rate,
                idle_time_minutes=kpi.idle_minutes
            )
        )
        total_prod += kpi.total_cycles
        total_expected += kpi.expected_cycles

    global_productivity = (total_prod / total_expected * 100) if total_expected else 0

    return DailyReport(
        date=report_date,
        machines=machine_reports,
        global_productivity=round(global_productivity,2)
    )
