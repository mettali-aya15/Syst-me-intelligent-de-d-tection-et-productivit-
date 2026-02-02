from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.event import Event
from app.schemas.detection import DetectionEventOut

router = APIRouter()

# Endpoint pour récupérer la liste des événements de détection
@router.get("/", response_model=List[DetectionEventOut])
def get_events(db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.event_time.desc()).limit(100).all()
