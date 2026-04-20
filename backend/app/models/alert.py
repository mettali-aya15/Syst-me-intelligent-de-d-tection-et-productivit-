#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les alertes
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
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
    message: str
    machine_id: Optional[str] = None
    employee_id: Optional[str] = None
    event_id: Optional[str] = None
    metadata: Optional[dict] = None


class Alert(BaseModel):
    """Alerte système"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    alert_type: str
    severity: AlertSeverity
    message: str
    machine_id: Optional[str] = None
    employee_id: Optional[str] = None
    event_id: Optional[str] = None
    metadata: Optional[dict] = None
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)