import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

"""
Demo simulator for Factory AI
Simulates IA events without camera
"""

import time
import random
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.event import Event
from app.models.production import ProductionCount
from app.models.workstation import Workstation
from app.models.alert import Alert
from app.services.realtime.websocket import WebSocketManager  # ✅ CORRIGÉ ICI

manager = WebSocketManager()  # ✅ CORRIGÉ ICI

# ... reste du code inchangé ...

def simulate_workstation(workstation: Workstation, db: Session):
    print(f"▶ Simulating workstation {workstation.identifier}")

    for _ in range(10):  # 10 cycles demo
        if workstation.workstation_type == "SEWING":
            working = random.choice([True, False, True])
            event_type = "EMPLOYEE_STARTED_WORK" if working else "EMPLOYEE_STOPPED_WORK"
        else:  # KNITTING
            working = random.choice([True, True, False])
            event_type = "WORKSTATION_ACTIVE" if working else "WORKSTATION_IDLE"

        event = Event(
            workstation_id=workstation.id,
            event_type=event_type,
            event_time=datetime.utcnow(),
            duration_seconds=random.randint(30, 300)
        )
        db.add(event)

        if working and workstation.workstation_type == "KNITTING":
            production = ProductionCount(
                workstation_id=workstation.id,
                quantity=random.randint(1, 5),
                recorded_at=datetime.utcnow()
            )
            db.add(production)

        db.commit()

        payload = {
            "workstation_id": workstation.id,
            "event": event_type,
            "timestamp": event.event_time.isoformat()
        }

        # Alert automatique
        if event_type in ["WORKSTATION_IDLE", "EMPLOYEE_STOPPED_WORK"]:
            alert = Alert(
                workstation_id=workstation.id,
                alert_type="workstation_idle",
                message="Workstation inactive détectée"
            )
            db.add(alert)
            db.commit()
            payload["alert"] = alert.message

        # Envoi temps réel
        try:
            import asyncio
            asyncio.run(manager.send_event(payload))
        except:
            pass

        time.sleep(random.randint(3, 6))  # simulate time passing

def run_demo():
    db: Session = SessionLocal()

    workstations = db.query(Workstation).all()

    print("🚀 Starting demo simulation...\n")

    for workstation in workstations:
        simulate_workstation(workstation, db)

    print("\n✅ Demo simulation completed")
    db.close()

if __name__ == "__main__":
    run_demo()