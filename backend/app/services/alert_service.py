#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de gestion des alertes
"""

from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.core.database import Database
from app.models.alert import AlertSeverity
from app.services.realtime.websocket import manager

import logging
logger = logging.getLogger(__name__)


class AlertService:
    """Service pour créer et gérer les alertes"""
    
    @staticmethod
    async def create_alert(
        alert_type: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        machine_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        video_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Créer une alerte et l'envoyer via WebSocket"""
        
        alert = {
            "alert_type": alert_type,
            "severity": severity.value,
            "title": title,
            "message": message,
            "machine_id": machine_id,
            "employee_id": employee_id,
            "video_id": video_id,
            "metadata": metadata or {},
            "is_resolved": False,
            "resolved_by": None,
            "resolved_at": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        collection = Database.get_collection("alerts")
        result = await collection.insert_one(alert)
        
        # Envoyer via WebSocket
        await manager.send_alert(
            alert_id=str(result.inserted_id),
            alert_type=alert_type,
            severity=severity.value,
            message=message,
            metadata=metadata
        )
        
        logger.info(f"🚨 Alerte créée : {title}")
        
        return str(result.inserted_id)
    
    @staticmethod
    async def alert_employee_absent(
        employee_id: str,
        employee_name: str,
        duration_minutes: int,
        video_id: Optional[str] = None
    ):
        """Alerte : employé absent"""
        severity = AlertSeverity.CRITICAL if duration_minutes > 60 else AlertSeverity.HIGH
        
        await AlertService.create_alert(
            alert_type="employee_absent",
            severity=severity,
            title="Employé absent détecté",
            message=f"L'employé {employee_name} n'a pas été détecté depuis {duration_minutes} minutes",
            employee_id=employee_id,
            video_id=video_id,
            metadata={
                "employee_name": employee_name,
                "duration_minutes": duration_minutes
            }
        )