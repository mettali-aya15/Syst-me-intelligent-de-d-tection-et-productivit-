#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles de détection Pydantic
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class BoundingBox(BaseModel):
    """Bounding box normalisée (0-1)"""
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
    """Détection d'un objet avec Track ID pour le suivi"""
    class_name: str
    confidence: float = Field(..., ge=0, le=1)
    bbox: BoundingBox
    source: str = "unknown"  # 'employee_model' or 'object_model'
    track_id: Optional[int] = None  # Crucial for ByteTrack


class FrameDetection(BaseModel):
    """Ensemble des détections pour une frame donnée"""
    frame_number: int
    timestamp: float
    detections: List[Detection]