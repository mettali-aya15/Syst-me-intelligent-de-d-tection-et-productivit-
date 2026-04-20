#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les vidéos
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum
from bson import ObjectId


class VideoStatus(str, Enum):
    """Statuts possibles d'une vidéo"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoCreate(BaseModel):
    """Modèle pour créer une vidéo"""
    filename: str
    file_path: str
    duration: float
    fps: int
    width: int
    height: int
    total_frames: int


class VideoUpload(BaseModel):
    """Modèle complet d'une vidéo uploadée"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(None, alias="_id")
    filename: str
    file_path: str
    annotated_path: Optional[str] = None
    duration: float
    fps: int
    width: int
    height: int
    total_frames: int
    status: VideoStatus = VideoStatus.UPLOADED
    total_detections: Optional[int] = None
    summary: Optional[dict] = None              # Total détections par classe
    unique_objects: Optional[dict] = None       # ✅ NOUVEAU - Objets uniques
    uploaded_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None