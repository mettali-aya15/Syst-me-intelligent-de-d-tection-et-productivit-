from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventOut

router = APIRouter()

# Endpoint pour récupérer la liste des événements
@router.get("/", response_model=List[EventOut])
def get_events(db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.event_time.desc()).limit(100).all()

# Endpoint pour récupérer les événements pour une workstation
@router.get("/workstations/{workstation_id}", response_model=List[EventOut])
def get_events_for_workstation(workstation_id: int, db: Session = Depends(get_db)):
    return db.query(Event).filter(Event.workstation_id == workstation_id).order_by(Event.event_time.desc()).limit(100).all()