#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les événements
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum
from bson import ObjectId


class EventType(str, Enum):
    """Types d'événements"""
    EMPLOYEE_ABSENT = "employee_absent"
    EMPLOYEE_LATE = "employee_late"
    TEMP_WORKER_DETECTED = "temp_worker_detected"
    MACHINE_STOPPED = "machine_stopped"
    MACHINE_LOW_ACTIVITY = "machine_low_activity"
    PRODUCTION_LOW = "production_low"
    PRODUCTION_HIGH = "production_high"
    TABLE_OCCUPIED = "table_occupied"
    TABLE_FREE = "table_free"
    ANOMALY_DETECTED = "anomaly_detected"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    VIDEO_PROCESSING_STARTED = "video_processing_started"
    VIDEO_PROCESSING_COMPLETED = "video_processing_completed"
    VIDEO_PROCESSING_FAILED = "video_processing_failed"
    ALERT_GENERATED = "alert_generated"


class EventCreate(BaseModel):
    """Données pour créer un événement"""
    type: EventType
    message: str
    severity: str = "info"
    employee_id: Optional[str] = None
    machine_id: Optional[str] = None
    video_id: Optional[str] = None
    metadata: Optional[dict] = None


class Event(BaseModel):
    """Événement système"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    type: EventType
    message: str
    severity: str = "info"
    employee_id: Optional[str] = None
    machine_id: Optional[str] = None
    video_id: Optional[str] = None
    metadata: Optional[dict] = None
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.now)