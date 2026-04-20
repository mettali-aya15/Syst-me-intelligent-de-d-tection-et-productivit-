#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les machines
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum
from bson import ObjectId


class MachineStatus(str, Enum):
    """Statuts possibles d'une machine"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    STOPPED = "stopped"


class MachineCreate(BaseModel):
    """Données pour créer une machine"""
    name: str
    type: str
    zone: str
    status: MachineStatus = MachineStatus.ACTIVE


class MachineUpdate(BaseModel):
    """Données pour mettre à jour une machine"""
    name: Optional[str] = None
    type: Optional[str] = None
    zone: Optional[str] = None
    status: Optional[MachineStatus] = None
    last_activity: Optional[datetime] = None


class Machine(BaseModel):
    """Machine"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    type: str
    zone: str
    status: MachineStatus = MachineStatus.ACTIVE
    last_activity: Optional[datetime] = None
    total_detections: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class MachineOut(BaseModel):
    """Machine (sortie API)"""
    _id: str
    name: str
    type: str
    zone: str
    status: str
    last_activity: Optional[datetime]
    total_detections: int
    created_at: datetime