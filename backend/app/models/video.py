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
    model_type: str = Field(default="both", description="Type de modèle: objects, employees, ou both")  # ✅ AJOUTÉ
    confidence: float = Field(default=0.3, description="Seuil de confiance pour la détection")  # ✅ AJOUTÉ
    total_detections: Optional[int] = None
    unique_objects: Optional[dict] = None       # Objets uniques
    uploaded_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    # ✅ CHAMPS POUR HASH + FLAGS
    video_hash: Optional[str] = Field(None, description="Hash MD5 du fichier vidéo")
    is_latest: bool = Field(True, description="Est la dernière version de cette vidéo")
    is_test: bool = Field(False, description="Vidéo de test (exclue des KPI)")
    is_demo: bool = Field(False, description="Vidéo de démo (exclue des KPI)")
    retest_count: int = Field(0, description="Nombre de fois réanalysée")
    last_reprocessed_at: Optional[datetime] = Field(None, description="Date de dernière réanalyse")
    original_processed_at: Optional[datetime] = Field(None, description="Date de première analyse")
