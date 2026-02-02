from datetime import datetime, timedelta

class KnittingMachineLogic:
    def __init__(self, machine_id: int):
        self.machine_id = machine_id
        self.state = "IDLE"
        self.last_motion_time = datetime.utcnow()
        self.idle_threshold = 60  # secondes

    def process_frame(self, detections):
        machine_motion = any(d['label'] == 'knitting_machine' for d in detections)
        now = datetime.utcnow()

        if machine_motion:
            if self.state != "ACTIVE":
                self.state = "ACTIVE"
                self.last_motion_time = now
                return {"machine_id": self.machine_id, "event": "MACHINE_STARTED", "time": now}
            else:
                self.last_motion_time = now
        else:
            if self.state == "ACTIVE" and (now - self.last_motion_time).total_seconds() > self.idle_threshold:
                self.state = "IDLE"
                return {"machine_id": self.machine_id, "event": "MACHINE_IDLE", "time": now}
        return None
