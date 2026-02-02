from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class DetectionEventCreate(BaseModel):
    camera_id: int
    machine_id: int
    event_type: Literal[
        "bag_detected",
        "machine_cycle",
        "employee_present",
        "employee_absent",
        "employee_sitting",
        "machine_idle"
    ]
    confidence: float


class DetectionEventOut(BaseModel):
    id: int
    camera_id: int
    machine_id: int
    event_type: str
    confidence: float
    timestamp: datetime

    class Config:
        from_attributes = True
