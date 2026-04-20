#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les employés
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from bson import ObjectId


class EmployeeCreate(BaseModel):
    """Données pour créer un employé"""
    name: str
    code: str
    role: str = "barista"
    is_temp: bool = False


class EmployeeUpdate(BaseModel):
    """Données pour mettre à jour un employé"""
    name: Optional[str] = None
    code: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_temp: Optional[bool] = None


class Employee(BaseModel):
    """Employé"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    code: str
    role: str = "barista"
    is_active: bool = True
    is_temp: bool = False
    last_seen: Optional[datetime] = None
    total_detections: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class EmployeeOut(BaseModel):
    """Employé (sortie API)"""
    _id: str
    name: str
    code: str
    role: str
    is_active: bool
    is_temp: bool
    last_seen: Optional[datetime]
    total_detections: int
    created_at: datetime