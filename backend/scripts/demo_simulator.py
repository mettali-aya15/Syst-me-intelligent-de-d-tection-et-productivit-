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
from app.models.machine import Machine
from app.models.alert import Alert
from app.services.realtime.websocket import ConnectionManager

manager = ConnectionManager()

def simulate_machine(machine: Machine, db: Session):
    print(f"▶ Simulating machine {machine.reference}")

    for _ in range(10):  # 10 cycles demo
        if machine.machine_type == "SEWING":
            working = random.choice([True, False, True])
            event_type = "EMPLOYEE_STARTED_WORK" if working else "EMPLOYEE_STOPPED_WORK"
        else:  # KNITTING
            working = random.choice([True, True, False])
            event_type = "MACHINE_ACTIVE" if working else "MACHINE_IDLE"

        event = Event(
            machine_id=machine.id,
            event_type=event_type,
            event_time=datetime.utcnow(),
            duration_seconds=random.randint(30, 300)
        )
        db.add(event)

        if working and machine.machine_type == "KNITTING":
            production = ProductionCount(
                machine_id=machine.id,
                quantity=random.randint(1, 5),
                recorded_at=datetime.utcnow()
            )
            db.add(production)

        db.commit()

        payload = {
            "machine_id": machine.id,
            "event": event_type,
            "timestamp": event.event_time.isoformat()
        }

        # Alert automatique
        if event_type in ["MACHINE_IDLE", "EMPLOYEE_STOPPED_WORK"]:
            alert = Alert(
                machine_id=machine.id,
                alert_type="machine_idle",
                message="Machine inactive détectée"
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

    machines = db.query(Machine).all()

    print("🚀 Starting demo simulation...\n")

    for machine in machines:
        simulate_machine(machine, db)

    print("\n✅ Demo simulation completed")
    db.close()

if __name__ == "__main__":
    run_demo()
