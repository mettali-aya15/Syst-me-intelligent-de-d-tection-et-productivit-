# schemas/detection.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DetectionBox(BaseModel):
    """📦 Une boîte de détection (bounding box)"""
    class_name: str           # ex: "client", "machine"
    confidence: float         # ex: 0.89 (89% de confiance)
    x: float                  # Position X (normalisée 0-1)
    y: float                  # Position Y
    width: float              # Largeur
    height: float             # Hauteur

class FrameDetection(BaseModel):
    """🖼️ Détections pour une frame vidéo"""
    frame_number: int         # Numéro de l'image dans la vidéo
    timestamp: float          # Temps en secondes
    detections: List[DetectionBox]

class VideoAnalysisRequest(BaseModel):
    """📤 Données envoyées pour analyser une vidéo"""
    video_path: str           # Chemin ou URL de la vidéo
    confidence: Optional[float] = 0.25

class VideoAnalysisResponse(BaseModel):
    """📥 Réponse de l'API après analyse"""
    video_name: str
    total_frames: int
    total_detections: int
    summary: dict             # Compte par classe
    results: List[FrameDetection]
    processed_at: datetime = Field(default_factory=datetime.now)