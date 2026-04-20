#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration de l'application
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Configuration globale de l'application"""
    
    # Autoriser les champs supplémentaires
    model_config = ConfigDict(extra='ignore')
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "camia_factory"
    
    # Modèles YOLO
    MODEL_EMPLOYEES_PATH: str = "data/models/best_person.pt"
    EMPLOYEE_MODEL_PATH: str = "data/models/best_person.pt"  # ✅ Changé ici
    OBJECT_MODEL_PATH: str = "data/models/best_objects.pt"
    MODEL_GENERAL_PATH: str = "data/models/best_objects.pt"  # ✅ Changé ici
    
    # Stockage
    UPLOAD_DIR: str = "data/videos"
    ANNOTATED_DIR: str = "data/annotated_videos"
    
    # Détection YOLO
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45
    
    # Production
    WORK_HOURS_PER_DAY: int = 8
    
    # Authentification JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 heures
    
    # Debug
    DEBUG: bool = True


settings = Settings()