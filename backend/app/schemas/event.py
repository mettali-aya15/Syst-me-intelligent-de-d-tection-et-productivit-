from datetime import datetime
from pydantic import BaseModel


class EventCreate(BaseModel):
    workstation_id: int
    employee_id: int
    event_type: str
    duration_seconds: int = 0
    event_time: datetime = None


class EventOut(BaseModel):
    id: int
    workstation_id: int
    employee_id: int
    event_type: str
    duration_seconds: int
    event_time: datetime

    class Config:
        orm_mode = True