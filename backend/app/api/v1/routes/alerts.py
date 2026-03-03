from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertOut

router = APIRouter()

# Endpoint pour récupérer la liste des alertes non résolues
@router.get("/", response_model=List[AlertOut])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).filter(Alert.is_resolved==False).order_by(Alert.created_at.desc()).all()