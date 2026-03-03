from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.camera import Camera
from app.models.site import Site
from app.schemas.camera import CameraOut

router = APIRouter()

# Endpoint to get all cameras
@router.get("/", response_model=List[CameraOut])
def get_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()

# Endpoint to get cameras for a site
@router.get("/sites/{site_id}/cameras", response_model=List[CameraOut])
def get_cameras_for_site(site_id: int, db: Session = Depends(get_db)):
    return db.query(Camera).filter(Camera.site_id == site_id).all()