from datetime import datetime

class SewingMachineLogic:
    def __init__(self, machine_id: int):
        self.machine_id = machine_id
        self.state = "IDLE"
        self.last_event_time = datetime.utcnow()

    def process_frame(self, detections):
        """
        detections: [{'label': 'person', 'bbox': [...]}]
        """
        person_detected = any(d['label'] == 'person' for d in detections)
        machine_active = any(d['label'] == 'sewing_machine' for d in detections)
        sitting = any(d['label'] == 'person' and d.get('sitting', False) for d in detections)

        now = datetime.utcnow()

        if person_detected and sitting and machine_active:
            if self.state != "WORKING":
                self.state = "WORKING"
                self.last_event_time = now
                return {"machine_id": self.machine_id, "event": "EMPLOYEE_STARTED_WORK", "time": now}
        else:
            if self.state == "WORKING":
                duration = (now - self.last_event_time).total_seconds()
                self.state = "IDLE"
                return {"machine_id": self.machine_id, "event": "EMPLOYEE_STOPPED_WORK", "duration": duration, "time": now}
        return None
