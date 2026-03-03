import cv2
from datetime import datetime
from app.services.ai.detector import YOLODetector
from app.services.ai.pose import is_sitting
from app.services.logic.sewing_logic import SewingMachineLogic
from app.services.logic.knitting_logic import KnittingMachineLogic
from app.db.session import SessionLocal
from app.models.event import Event
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.workstation import Machine
from app.services.realtime.websocket import manager

class RTSPWorker:
    def __init__(self, camera: Camera, machine: Machine):
        self.camera = camera
        self.machine = machine
        self.detector = YOLODetector(device="cuda")
        self.logic = (
            SewingMachineLogic()
            if machine.machine_type == "sewing"
            else KnittingMachineLogic()
        )

    def run(self):
        cap = cv2.VideoCapture(self.camera.rtsp_url)
        db = SessionLocal()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue

            detections = self.detector.detect(frame)

            person_present = False
            sitting = False
            motion = False

            for d in detections:
                if d["label"] == "person":
                    person_present = True
                    sitting = is_sitting(d["bbox"])
                if d["label"] in ["machine", "motor"]:
                    motion = True

            event_data = (
                self.logic.process(person_present, sitting)
                if self.machine.machine_type == "sewing"
                else self.logic.process(motion)
            )

            if event_data:
                event = Event(
                    machine_id=self.machine.id,
                    event_type=event_data["event"],
                    event_time=datetime.utcnow(),
                    duration_seconds=event_data.get("duration", 0)
                )
                db.add(event)
                db.commit()

                payload = {
                    "machine": self.machine.id,
                    "event": event.event_type,
                    "time": event.event_time.isoformat()
                }

                if event.event_type in ["MACHINE_IDLE", "EMPLOYEE_STOPPED_WORK"]:
                    alert = Alert(
                        machine_id=self.machine.id,
                        alert_type="idle",
                        message="Arrêt machine détecté"
                    )
                    db.add(alert)
                    db.commit()
                    payload["alert"] = alert.message

                import asyncio
                asyncio.run(manager.broadcast(payload))
