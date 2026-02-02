"""
Seed initial data for Factory AI system
"""

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.factory import Factory
from app.models.camera import Camera
from app.models.machine import Machine

def seed():
    db: Session = SessionLocal()
    print("⏳ Inserting seed data...")

    # Factory
    factory = Factory(
        name="Demo Factory",
        location="Tunis"
    )
    db.add(factory)
    db.commit()
    db.refresh(factory)

    # Cameras
    camera1 = Camera(
        factory_id=factory.id,
        name="Camera Sewing 1",
        rtsp_url="rtsp://demo_camera_1",
        zone="Sewing Line A"
    )

    camera2 = Camera(
        factory_id=factory.id,
        name="Camera Knitting 1",
        rtsp_url="rtsp://demo_camera_2",
        zone="Knitting Zone"
    )

    db.add_all([camera1, camera2])
    db.commit()

    # Machines
    sewing_machine = Machine(
        camera_id=camera1.id,
        machine_type="SEWING",
        reference="SW-01",
        location="Line A - Seat 1"
    )

    knitting_machine = Machine(
        camera_id=camera2.id,
        machine_type="KNITTING",
        reference="KN-01",
        location="Zone B"
    )

    db.add_all([sewing_machine, knitting_machine])
    db.commit()

    print("✅ Seed data inserted successfully")
    db.close()

if __name__ == "__main__":
    seed()
