#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les alertes
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from bson import ObjectId


class AlertSeverity(str, Enum):
    """Sévérité des alertes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCreate(BaseModel):
    """Données pour créer une alerte"""
    alert_type: str
    severity: AlertSeverity
    title: str  # ✅ AJOUTÉ
    message: str
    machine_id: Optional[str] = None
    employee_id: Optional[str] = None
    video_id: Optional[str] = None  # ✅ AJOUTÉ
    event_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Alert(BaseModel):
    """Alerte système"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    alert_type: str
    severity: AlertSeverity
    title: str  # ✅ AJOUTÉ
    message: str
    machine_id: Optional[str] = None
    employee_id: Optional[str] = None
    video_id: Optional[str] = None  # ✅ AJOUTÉ
    event_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)  # ✅ AJOUTÉ