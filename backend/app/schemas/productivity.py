from pydantic import BaseModel
from datetime import date


class ProductivityKPI(BaseModel):
    machine_id: int
    date: date

    total_cycles: int
    expected_cycles: int

    productivity_rate: float  # %
    idle_minutes: float
    active_minutes: float
