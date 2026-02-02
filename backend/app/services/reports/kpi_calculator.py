from sqlalchemy.orm import Session
from datetime import date
from app.models.production import ProductionCount
from app.models.event import Event
from app.schemas.productivity import ProductivityKPI

def calculate_kpi(db: Session, machine_id: int, report_date: date) -> ProductivityKPI:
    # Production totale du jour
    total_prod = db.query(ProductionCount).filter(
        ProductionCount.machine_id == machine_id,
        ProductionCount.recorded_at.cast(date) == report_date
    ).with_entities(
        ProductionCount.quantity
    ).all()

    total_qty = sum(q[0] for q in total_prod) if total_prod else 0

    # Temps actif et idle
    events = db.query(Event).filter(
        Event.machine_id == machine_id,
        Event.event_time.cast(date) == report_date
    ).all()

    active_seconds = sum(e.duration_seconds for e in events if e.event_type in ["MACHINE_ACTIVE","EMPLOYEE_STARTED_WORK"])
    idle_seconds = sum(e.duration_seconds for e in events if e.event_type in ["MACHINE_IDLE","EMPLOYEE_STOPPED_WORK"])

    expected_cycles = max(1, total_qty)  # simplification demo
    productivity_rate = (active_seconds / (active_seconds + idle_seconds)) * 100 if (active_seconds + idle_seconds) > 0 else 0

    return ProductivityKPI(
        machine_id=machine_id,
        date=report_date,
        total_cycles=total_qty,
        expected_cycles=expected_cycles,
        productivity_rate=round(productivity_rate,2),
        active_minutes=round(active_seconds/60,2),
        idle_minutes=round(idle_seconds/60,2)
    )
