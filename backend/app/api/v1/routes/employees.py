from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.employee import Employee
from app.schemas.employee import EmployeeOut

router = APIRouter()

# Endpoint pour récupérer la liste des employés
@router.get("/", response_model=List[EmployeeOut])
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()
