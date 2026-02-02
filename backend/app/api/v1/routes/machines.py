from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.machine import Machine
from app.schemas.machine import MachineOut

router = APIRouter()

# Endpoint pour récupérer toutes les machines
@router.get("/", response_model=List[MachineOut])
def get_machines(db: Session = Depends(get_db)):
    return db.query(Machine).all()
