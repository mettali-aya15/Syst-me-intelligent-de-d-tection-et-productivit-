from pydantic import BaseModel
from typing import Literal, Optional


class MachineCreate(BaseModel):
    name: str
    type: Literal["sewing", "knitting"]
    expected_cycle_seconds: int
    location: Optional[str]


class MachineOut(BaseModel):
    id: int
    name: str
    type: str
    expected_cycle_seconds: int
    is_active: bool

    class Config:
        from_attributes = True
