from pydantic import BaseModel
from datetime import date
from typing import List


class MachineReport(BaseModel):
    machine_name: str
    total_output: int
    productivity_rate: float
    idle_time_minutes: float


class DailyReport(BaseModel):
    date: date
    machines: List[MachineReport]
    global_productivity: float
