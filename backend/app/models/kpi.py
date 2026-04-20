#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les KPIs
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import List, Optional
from bson import ObjectId


class EmployeeMetrics(BaseModel):
    """Métriques employés"""
    total: int = 0
    present: int = 0
    absent: int = 0
    temp_workers: int = 0


class MachineMetrics(BaseModel):
    """Métriques machines"""
    total: int = 0
    active: int = 0
    stopped: int = 0


class TableMetrics(BaseModel):
    """Métriques tables"""
    total: int = 0
    occupied: int = 0
    free: int = 0


class ProductionMetrics(BaseModel):
    """Métriques production"""
    total_produced: int = 0
    hourly_rate: float = 0.0


class KPISnapshot(BaseModel):
    """Snapshot KPI horaire"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    date: date
    hour: int
    employees: EmployeeMetrics
    machines: MachineMetrics
    tables: TableMetrics
    production: ProductionMetrics
    productivity_rate: float = 0.0
    video_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)


class DailyReport(BaseModel):
    """Rapport journalier"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    date: date
    summary: dict = {}
    employees_present: List[str] = []
    employees_absent: List[str] = []
    total_videos_processed: int = 0
    total_detections: int = 0
    productivity_score: float = 0.0
    hourly_snapshots: List[dict] = []
    generated_at: datetime = Field(default_factory=datetime.now)