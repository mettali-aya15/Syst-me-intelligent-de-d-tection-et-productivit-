from datetime import datetime
from pydantic import BaseModel


class BaseSchema(BaseModel):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
