#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constructeur d'événements système
Crée des événements basés sur les détections et règles métier
"""

from typing import List, Dict, Optional
from datetime import datetime
from bson import ObjectId

from app.models.event import Event, EventCreate, EventType
from app.models.alert import Alert, AlertCreate, AlertSeverity
from core.database import Database

import logging
logger = logging.getLogger(__name__)


class EventBuilder:
    """Constructeur d'événements système"""
    
    @staticmethod
    async def create_event(
        event_type: EventType,
        message: str,
        severity: str = "info",
        employee_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        video_id: Optional[str] = None,
        metadata: Dict = None
    ) -> Event:
        """
        Créer un événement système
        
        Args:
            event_type: Type d'événement
            message: Message descriptif
            severity: "info", "warning", "critical"
            employee_id: ID employé (optionnel)
            machine_id: ID machine (optionnel)
            video_id: ID vidéo (optionnel)
            metadata: Données additionnelles
        
        Returns:
            Event créé
        """
        try:
            event_data = EventCreate(
                type=event_type,
                employee_id=ObjectId(employee_id) if employee_id else None,
                machine_id=ObjectId(machine_id) if machine_id else None,
                video_id=ObjectId(video_id) if video_id else None,
                message=message,
                severity=severity,
                metadata=metadata or {}
            )
            
            event = Event(**event_data.dict())
            
            # Sauvegarder en DB
            collection = Database.get_collection("events")
            event_dict = event.dict(by_alias=True, exclude={"id"})
            result = await collection.insert_one(event_dict)
            
            event.id = result.inserted_id
            
            logger.info(f"✅ Événement créé : {event_type} - {message}")
            
            # Créer alerte si sévérité haute
            if severity in ["warning", "critical"]:
                await EventBuilder._create_alert_from_event(event)
            
            return event
        
        except Exception as e:
            logger.error(f"❌ Erreur création événement : {e}")
            raise
    
    @staticmethod
    async def _create_alert_from_event(event: Event) -> Alert:
        """
        Créer une alerte à partir d'un événement
        
        Args:
            event: Événement source
        
        Returns:
            Alert créée
        """
        # Mapper sévérité
        severity_map = {
            "info": AlertSeverity.LOW,
            "warning": AlertSeverity.MEDIUM,
            "critical": AlertSeverity.HIGH
        }
        
        alert_severity = severity_map.get(event.severity, AlertSeverity.MEDIUM)
        
        # Déterminer le type d'alerte
        alert_type_map = {
            EventType.EMPLOYEE_ABSENT: "employee_absent",
            EventType.MACHINE_STOPPED: "machine_stopped",
            EventType.MACHINE_MAINTENANCE: "machine_maintenance",
            EventType.PRODUCTION_LOW: "production_low",
            EventType.ANOMALY_DETECTED: "anomaly"
        }
        
        alert_type = alert_type_map.get(event.type, "general")
        
        alert_data = AlertCreate(
            alert_type=alert_type,
            severity=alert_severity,
            machine_id=event.machine_id,
            employee_id=event.employee_id,
            event_id=event.id,
            message=event.message,
            description=f"Événement: {event.type}"
        )
        
        alert = Alert(**alert_data.dict())
        
        # Sauvegarder en DB
        collection = Database.get_collection("alerts")
        alert_dict = alert.dict(by_alias=True, exclude={"id"})
        result = await collection.insert_one(alert_dict)
        
        alert.id = result.inserted_id
        
        logger.info(f"🚨 Alerte créée : {alert_type} - {alert_severity}")
        
        return alert
    
    @staticmethod
    async def detect_employee_absence(expected_employees: List[str], detected_employees: List[str]) -> List[Event]:
        """
        Détecter les absences d'employés
        
        Args:
            expected_employees: Liste des employés attendus
            detected_employees: Liste des employés détectés
        
        Returns:
            Liste d'événements créés
        """
        events = []
        
        for employee_name in expected_employees:
            if employee_name not in detected_employees:
                # Récupérer l'ID de l'employé
                employees_collection = Database.get_collection("employees")
                employee_doc = await employees_collection.find_one({"name": employee_name})
                
                if employee_doc:
                    event = await EventBuilder.create_event(
                        event_type=EventType.EMPLOYEE_ABSENT,
                        message=f"Employé absent détecté : {employee_name}",
                        severity="warning",
                        employee_id=str(employee_doc["_id"])
                    )
                    events.append(event)
        
        return events
    
    @staticmethod
    async def detect_machine_stoppage(
        machine_name: str,
        machine_id: str,
        duration_minutes: float
    ) -> Event:
        """
        Détecter un arrêt machine
        
        Args:
            machine_name: Nom de la machine
            machine_id: ID de la machine
            duration_minutes: Durée d'arrêt estimée
        
        Returns:
            Event créé
        """
        severity = "critical" if duration_minutes > 30 else "warning"
        
        event = await EventBuilder.create_event(
            event_type=EventType.MACHINE_STOPPED,
            message=f"Machine arrêtée : {machine_name} (durée estimée: {duration_minutes:.1f} min)",
            severity=severity,
            machine_id=machine_id,
            metadata={
                "duration_minutes": duration_minutes,
                "machine_name": machine_name
            }
        )
        
        return event
    
    @staticmethod
    async def detect_production_anomaly(
        production_rate: float,
        expected_rate: float,
        video_id: str
    ) -> Optional[Event]:
        """
        Détecter une anomalie de production
        
        Args:
            production_rate: Taux de production actuel
            expected_rate: Taux attendu
            video_id: ID de la vidéo analysée
        
        Returns:
            Event créé ou None
        """
        deviation = abs(production_rate - expected_rate) / expected_rate
        
        if deviation > 0.3:  # 30% de déviation
            severity = "critical" if deviation > 0.5 else "warning"
            
            event = await EventBuilder.create_event(
                event_type=EventType.PRODUCTION_LOW if production_rate < expected_rate else EventType.PRODUCTION_HIGH,
                message=f"Anomalie de production détectée : {production_rate:.1f} vs {expected_rate:.1f} attendu",
                severity=severity,
                video_id=video_id,
                metadata={
                    "production_rate": production_rate,
                    "expected_rate": expected_rate,
                    "deviation": round(deviation * 100, 2)
                }
            )
            
            return event
        
        return None