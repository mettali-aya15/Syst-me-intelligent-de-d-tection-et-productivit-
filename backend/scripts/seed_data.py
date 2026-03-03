"""
Seed initial data for Factory AI system
"""

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.site import Site
from app.models.camera import Camera
from app.models.workstation import Workstation

def seed():
    db: Session = SessionLocal()
    print("⏳ Inserting seed data...")

    # Site
    site = Site(
        name="Demo Site",
        location="Tunis"
    )
    db.add(site)
    db.commit()
    db.refresh(site)

    # Cameras
    camera1 = Camera(
        site_id=site.id,
        name="Camera Sewing 1",
        rtsp_url="rtsp://demo_camera_1",
        zone="Sewing Line A"
    )

    camera2 = Camera(
        site_id=site.id,
        name="Camera Knitting 1",
        rtsp_url="rtsp://demo_camera_2",
        zone="Knitting Zone"
    )

    db.add_all([camera1, camera2])
    db.commit()

    # Workstations
    sewing_workstation = Workstation(
        camera_id=camera1.id,
        workstation_type="SEWING",
        identifier="SW-01",
        zone="Line A - Seat 1"
    )

    knitting_workstation = Workstation(
        camera_id=camera2.id,
        workstation_type="KNITTING",
        identifier="KN-01",
        zone="Zone B"
    )

    db.add_all([sewing_workstation, knitting_workstation])
    db.commit()

    print("✅ Seed data inserted successfully")
    db.close()

if __name__ == "__main__":
    seed()