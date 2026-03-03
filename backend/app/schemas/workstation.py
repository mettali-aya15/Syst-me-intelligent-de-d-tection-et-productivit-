

from datetime import datetime
from pydantic import BaseModel


class WorkstationCreate(BaseModel):
    name: str
    factory_id: int


class WorkstationOut(BaseModel):
    id: int
    name: str
    factory_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True