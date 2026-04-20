#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les détections
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from bson import ObjectId


class BoundingBox(BaseModel):
    """Boîte englobante (coordonnées normalisées)"""
    x: float = Field(..., ge=0, le=1)
    y: float = Field(..., ge=0, le=1)
    width: float = Field(..., ge=0, le=1)
    height: float = Field(..., ge=0, le=1)


class Detection(BaseModel):
    """Détection individuelle"""
    class_name: str
    confidence: float = Field(..., ge=0, le=1)
    bbox: BoundingBox
    source: str


class FrameDetection(BaseModel):
    """Détections d'une frame"""
    frame_number: int
    timestamp: float
    detections: List[Detection]


class VideoDetection(BaseModel):
    """Détection enregistrée en base"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    video_id: ObjectId
    frame_number: int
    timestamp: float
    class_name: str
    confidence: float
    bbox: BoundingBox
    source: str
    processed_at: datetime = Field(default_factory=datetime.now)


class DetectionSummary(BaseModel):
    """Résumé des détections"""
    total_detections: int
    by_class: dict
    by_source: dict