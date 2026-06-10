#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les notifications
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class NotificationCreate(BaseModel):
    """Données pour créer une notification"""
    type: str
    severity: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class Notification(BaseModel):
    """Notification système"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    type: str  # "alert", "kpi_update", "video_complete", "video_failed", etc.
    severity: str  # "low", "medium", "high", "critical"
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class NotificationOut(BaseModel):
    """Notification (sortie API)"""
    _id: str
    type: str
    severity: str
    title: str
    message: str
    data: Dict[str, Any]
    read: bool
    read_at: Optional[datetime]
    created_at: datetime
