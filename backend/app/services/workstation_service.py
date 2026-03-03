from sqlalchemy.orm import Session
from app.models.workstation import Workstation
from app.models.camera import Camera
from app.models.report import DailyReport
from app.models.production import ProductionCount
from app.models.event import Event
from app.models.alert import Alert
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.session import get_db


def get_workstation_by_id(workstation_id: int) -> Workstation:
    """Récupère une workstation par son ID"""
    db = get_db()
    return db.query(Workstation).filter(Workstation.id == workstation_id).first()

def calculate_workstation_productivity(workstation_id: int) -> float:
    """Calcule la productivité d'une workstation"""
    db = get_db()
    reports = db.query(DailyReport).filter(
        DailyReport.workstation_id == workstation_id
    ).all()
    
    total_working_time = sum(report.working_time_seconds for report in reports)
    total_idle_time = sum(report.idle_time_seconds for report in reports)
    
    if total_working_time + total_idle_time == 0:
        return 0.0
    
    return (total_working_time / (total_working_time + total_idle_time)) * 100

def get_workstation(db: Session, workstation_id: int) -> Optional[Workstation]:
    """Récupère une workstation par son ID"""
    return db.query(Workstation).filter(Workstation.id == workstation_id).first()

def get_workstations(db: Session, skip: int = 0, limit: int = 100) -> List[Workstation]:
    """Récupère toutes les workstations avec pagination"""
    return db.query(Workstation).offset(skip).limit(limit).all()

def get_workstations_by_type(db: Session, workstation_type: str) -> List[Workstation]:
    """Récupère les workstations par type"""
    return db.query(Workstation).filter(Workstation.workstation_type == workstation_type).all()

def create_workstation(db: Session, camera_id: int, workstation_type: str, identifier: str, zone: str) -> Workstation:
    """Crée une nouvelle workstation"""
    new_workstation = Workstation(
        camera_id=camera_id,
        workstation_type=workstation_type,
        identifier=identifier,
        zone=zone
    )
    db.add(new_workstation)
    db.commit()
    db.refresh(new_workstation)
    return new_workstation

def update_workstation(db: Session, workstation_id: int, workstation_type: str = None, identifier: str = None, zone: str = None) -> Optional[Workstation]:
    """Met à jour une workstation existante"""
    workstation = get_workstation(db, workstation_id)
    if workstation:
        if workstation_type:
            workstation.workstation_type = workstation_type
        if identifier:
            workstation.identifier = identifier
        if zone:
            workstation.zone = zone
        db.commit()
        db.refresh(workstation)
    return workstation

def delete_workstation(db: Session, workstation_id: int) -> bool:
    """Supprime une workstation"""
    workstation = get_workstation(db, workstation_id)
    if workstation:
        db.delete(workstation)
        db.commit()
        return True
    return False

def calculate_workstation_productivity(db: Session, workstation_id: int, days: int = 7) -> float:
    """Calcule la productivité d'une workstation sur une période"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    reports = db.query(DailyReport).filter(
        DailyReport.workstation_id == workstation_id,
        DailyReport.report_date >= start_date.date(),
        DailyReport.report_date <= end_date.date()
    ).all()
    
    if not reports:
        return 0.0
    
    total_working_time = sum(report.working_time_seconds for report in reports)
    total_idle_time = sum(report.idle_time_seconds for report in reports)
    
    total_time = total_working_time + total_idle_time
    if total_time == 0:
        return 0.0
    
    return (total_working_time / total_time) * 100

def get_workstation_production(db: Session, workstation_id: int, days: int = 7) -> int:
    """Récupère la production totale d'une workstation sur une période"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    production_counts = db.query(ProductionCount).filter(
        ProductionCount.workstation_id == workstation_id,
        ProductionCount.recorded_at >= start_date,
        ProductionCount.recorded_at <= end_date
    ).all()
    
    return sum(pc.quantity for pc in production_counts)

def get_workstation_alerts(db: Session, workstation_id: int, days: int = 7) -> List[Alert]:
    """Récupère les alertes d'une workstation sur une période"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    return db.query(Alert).filter(
        Alert.workstation_id == workstation_id,
        Alert.created_at >= start_date,
        Alert.created_at <= end_date
    ).all()

def get_workstation_events(db: Session, workstation_id: int, days: int = 7) -> List[Event]:
    """Récupère les événements d'une workstation sur une période"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    return db.query(Event).filter(
        Event.workstation_id == workstation_id,
        Event.event_time >= start_date,
        Event.event_time <= end_date
    ).all()

def get_workstation_stats(db: Session, workstation_id: int) -> dict:
    """Récupère les statistiques complètes d'une workstation"""
    productivity = calculate_workstation_productivity(db, workstation_id)
    production = get_workstation_production(db, workstation_id)
    alerts = get_workstation_alerts(db, workstation_id)
    events = get_workstation_events(db, workstation_id)
    
    return {
        "productivity": round(productivity, 2),
        "total_production": production,
        "total_alerts": len(alerts),
        "total_events": len(events),
        "high_severity_alerts": sum(1 for a in alerts if a.severity == "HIGH")
    }