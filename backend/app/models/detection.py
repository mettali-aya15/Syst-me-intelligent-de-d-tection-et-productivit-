#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modeles de detection Pydantic
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class BoundingBox(BaseModel):
    """Bounding box normalisee (0-1)"""
    x: float = Field(..., ge=0, le=1)
    y: float = Field(..., ge=0, le=1)
    width: float = Field(..., ge=0, le=1)
    height: float = Field(..., ge=0, le=1)
    
    @property
    def x1(self) -> float:
        return self.x
    
    @property
    def y1(self) -> float:
        return self.y
    
    @property
    def x2(self) -> float:
        return self.x + self.width
    
    @property
    def y2(self) -> float:
        return self.y + self.height


class Detection(BaseModel):
    """Detection d'un objet avec Track ID pour le suivi"""
    class_name: str
    confidence: float = Field(..., ge=0, le=1)
    bbox: BoundingBox
    source: str = "unknown"
    classes_detectees: Optional[dict] = None
    track_id: Optional[int] = None


class FrameDetection(BaseModel):
    """Ensemble des detections pour une frame donnee"""
    frame_number: int
    timestamp: float
    detections: List[Detection]