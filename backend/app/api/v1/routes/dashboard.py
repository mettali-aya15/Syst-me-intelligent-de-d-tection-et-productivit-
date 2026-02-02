from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date, datetime, timedelta

from app.db.session import get_db
from app.models import event, machine

router = APIRouter()

# Endpoint to get global KPIs for the dashboard - Taux de productivité global
@router.get("/kpis/global")
def global_kpis(db: Session = Depends(get_db)):

    today = date.today()

    total_cycles = db.query(func.count()).filter(
        event.event_type == "machine_cycle",
        func.date(event.timestamp) == today
    ).scalar()

    idle_events = db.query(func.count()).filter(
        event.event_type == "machine_idle",
        func.date(event.timestamp) == today
    ).scalar()

    return {
        "date": today,
        "total_cycles": total_cycles,
        "idle_events": idle_events,
        "global_productivity_rate": round(
            total_cycles / max((total_cycles + idle_events), 1) * 100, 2
        )
    }

# Endpoint to get machine KPIs for the dashboard - Taux de productivité des machines
@router.get("/kpis/machines")
def machines_kpis(db: Session = Depends(get_db)):

    today = date.today()

    results = (
        db.query(
            machine.id,
            machine.name,
            machine.type,
            func.count(
                case((event.event_type == "machine_cycle", 1))
            ).label("cycles"),
            func.count(
                case((event.event_type == "machine_idle", 1))
            ).label("idle")
        )
        .join(event, event.machine_id == machine.id)
        .filter(func.date(event.timestamp) == today)
        .group_by(machine.id)
        .all()
    )

    data = []
    for r in results:
        productivity = r.cycles / max((r.cycles + r.idle), 1) * 100

        data.append({
            "machine_id": r.id,
            "machine_name": r.name,
            "type": r.type,
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
            event.machine_id,
            func.count(
                case((event.event_type == "employee_sitting", 1))
            ).label("sitting_events"),
            func.count(
                case((event.event_type == "employee_absent", 1))
            ).label("absent_events"),
        )
        .filter(func.date(event.timestamp) == today)
        .group_by(event.machine_id)
        .all()
    )

    return [
        {
            "machine_id": r.machine_id,
            "sitting_events": r.sitting_events,
            "absent_events": r.absent_events,
            "presence_rate": round(
                r.sitting_events /
                max((r.sitting_events + r.absent_events), 1) * 100, 2
            )
        }
        for r in results
    ]

# Endpoint to get daily machine cycles for the dashboard - Production par heure
@router.get("/charts/hourly-production")
def hourly_production(db: Session = Depends(get_db)):

    today = date.today()

    results = (
        db.query(
            func.extract('hour', event.timestamp).label("hour"),
            func.count().label("cycles")
        )
        .filter(
            event.event_type == "machine_cycle",
            func.date(event.timestamp) == today
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
            "machine_idle",
            "employee_absent"
        ]),
        event.timestamp >= datetime.now() - timedelta(minutes=30)
    ).all()

    return [
        {
            "machine_id": a.machine_id,
            "event": a.event_type,
            "time": a.timestamp
        }
        for a in alerts
    ]
