from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.camera import Camera
from app.schemas.camera import CameraOut

router = APIRouter()

# Endpoint to get all cameras
@router.get("/", response_model=List[CameraOut])
def get_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()
