from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.workstation import Workstation
from app.schemas.workstation import WorkstationOut

router = APIRouter()

# Endpoint pour récupérer toutes les workstations
@router.get("/", response_model=List[WorkstationOut])
def get_workstations(db: Session = Depends(get_db)):
    return db.query(Workstation).all()