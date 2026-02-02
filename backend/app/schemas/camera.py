from pydantic import BaseModel
from typing import Optional


class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    location: Optional[str]
    machine_id: Optional[int]


class CameraOut(BaseModel):
    id: int
    name: str
    location: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
