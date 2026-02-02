from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class AlertOut(BaseModel):
    id: int
    machine_id: int
    alert_type: Literal[
        "machine_idle",
        "low_productivity",
        "employee_absent",
        "camera_offline"
    ]
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
