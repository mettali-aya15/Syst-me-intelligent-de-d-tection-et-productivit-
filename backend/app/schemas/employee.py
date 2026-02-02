from pydantic import BaseModel
from typing import Optional


class EmployeeCreate(BaseModel):
    full_name: str
    badge_id: str
    assigned_machine_id: Optional[int]


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    badge_id: str
    is_present: bool

    class Config:
        from_attributes = True
