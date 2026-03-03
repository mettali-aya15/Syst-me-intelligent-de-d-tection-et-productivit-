from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date, datetime, timedelta

from app.db.session import get_db
from app.models import event
from app.models.workstation import Workstation

router = APIRouter()

# Endpoint to get global KPIs for the dashboard - Taux de productivité global
@router.get("/kpis/global")
def global_kpis(db: Session = Depends(get_db)):
    today = date.today()

    total_cycles = db.query(func.count()).filter(
        event.event_type == "workstation_active",
        func.date(event.event_time) == today
    ).scalar()

    idle_events = db.query(func.count()).filter(
        event.event_type == "workstation_idle",
        func.date(event.event_time) == today
    ).scalar()

    return {
        "date": today,
        "total_cycles": total_cycles,
        "idle_events": idle_events,
        "global_productivity_rate": round(
            total_cycles / max((total_cycles + idle_events), 1) * 100, 2
        )
    }

# Endpoint to get workstation KPIs for the dashboard - Taux de productivité des workstations
@router.get("/kpis/workstations")
def workstations_kpis(db: Session = Depends(get_db)):
    today = date.today()

    results = (
        db.query(
            Workstation.id,
            Workstation.identifier,
            Workstation.workstation_type,
            func.count(
                case((event.event_type == "workstation_active", 1))
            ).label("cycles"),
            func.count(
                case((event.event_type == "workstation_idle", 1))
            ).label("idle")
        )
        .join(event, event.workstation_id == Workstation.id)
        .filter(func.date(event.event_time) == today)
        .group_by(Workstation.id)
        .all()
    )

    data = []
    for r in results:
        productivity = r.cycles / max((r.cycles + r.idle), 1) * 100

        data.append({
            "workstation_id": r.id,
            "workstation_name": r.identifier,
            "type": r.workstation_type,
            "cycles": r.cycles,
            "idle_events": r.idle,
            "productivity_rate": round(productivity, 2)
        })

    return data

# Endpoint to get employee time tracking KPIs for the dashboard - Taux de présence des employés
@router.get("/kpis/employees")
def employee_time_tracking(db: Session = Depends(get_db)):
    today = date.today()

    results = (
        db.query(
            event.workstation_id,
            func.count(
                case((event.event_type == "employee_started_work", 1))
            ).label("working_events"),
            func.count(
                case((event.event_type == "employee_stopped_work", 1))
            ).label("idle_events"),
        )
        .filter(func.date(event.event_time) == today)
        .group_by(event.workstation_id)
        .all()
    )

    return [
        {
            "workstation_id": r.workstation_id,
            "working_events": r.working_events,
            "idle_events": r.idle_events,
            "presence_rate": round(
                r.working_events /
                max((r.working_events + r.idle_events), 1) * 100, 2
            )
        }
        for r in results
    ]

# Endpoint to get daily workstation cycles for the dashboard - Production par heure
@router.get("/charts/hourly-production")
def hourly_production(db: Session = Depends(get_db)):
    today = date.today()

    results = (
        db.query(
            func.extract('hour', event.event_time).label("hour"),
            func.count().label("cycles")
        )
        .filter(
            event.event_type == "workstation_active",
            func.date(event.event_time) == today
        )
        .group_by("hour")
        .order_by("hour")
        .all()
    )

    return [
        {"hour": int(r.hour), "cycles": r.cycles}
        for r in results
    ]

# Endpoint to get active alerts for the dashboard
@router.get("/alerts/active")
def active_alerts(db: Session = Depends(get_db)):
    alerts = db.query(event).filter(
        event.event_type.in_([
            "workstation_idle",
            "employee_absent"
        ]),
        event.event_time >= datetime.now() - timedelta(minutes=30)
    ).all()

    return [
        {
            "workstation_id": a.workstation_id,
            "event": a.event_type,
            "time": a.event_time
        }
        for a in alerts
    ]