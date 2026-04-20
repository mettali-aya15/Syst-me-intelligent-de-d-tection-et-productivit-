#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Règles métier du système
Logique de validation et règles de gestion
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)


class BusinessRules:
    """Règles métier de CAMIA-Factory"""
    
    # SEUILS DE DÉTECTION
    MIN_CONFIDENCE = 0.3
    OPTIMAL_CONFIDENCE = 0.5
    HIGH_CONFIDENCE = 0.7
    
    # PRODUCTIVITÉ
    MIN_EMPLOYEES_REQUIRED = 2
    MAX_EMPLOYEES_CAPACITY = 10
    MIN_MACHINES_ACTIVE = 1
    
    # TEMPS
    MAX_MACHINE_DOWNTIME_MINUTES = 30
    MAX_EMPLOYEE_ABSENCE_HOURS = 2
    WORK_HOURS_START = 8  # 8h
    WORK_HOURS_END = 17   # 17h
    
    # TABLES (CAFÉ)
    MAX_TABLE_OCCUPATION_MINUTES = 90
    
    @staticmethod
    def is_valid_detection_confidence(confidence: float) -> bool:
        """Vérifier si la confiance est acceptable"""
        return confidence >= BusinessRules.MIN_CONFIDENCE
    
    @staticmethod
    def is_high_quality_detection(confidence: float) -> bool:
        """Vérifier si la détection est de haute qualité"""
        return confidence >= BusinessRules.HIGH_CONFIDENCE
    
    @staticmethod
    def is_sufficient_workforce(employee_count: int) -> bool:
        """Vérifier si le nombre d'employés est suffisant"""
        return employee_count >= BusinessRules.MIN_EMPLOYEES_REQUIRED
    
    @staticmethod
    def is_overloaded_workforce(employee_count: int) -> bool:
        """Vérifier si trop d'employés (surcharge)"""
        return employee_count > BusinessRules.MAX_EMPLOYEES_CAPACITY
    
    @staticmethod
    def is_critical_machine_downtime(downtime_minutes: float) -> bool:
        """Vérifier si l'arrêt machine est critique"""
        return downtime_minutes > BusinessRules.MAX_MACHINE_DOWNTIME_MINUTES
    
    @staticmethod
    def is_working_hours(check_time: datetime = None) -> bool:
        """Vérifier si on est dans les heures de travail"""
        if check_time is None:
            check_time = datetime.now()
        
        hour = check_time.hour
        return BusinessRules.WORK_HOURS_START <= hour < BusinessRules.WORK_HOURS_END
    
    @staticmethod
    def calculate_productivity_grade(score: float) -> str:
        """
        Calculer la note de productivité
        
        Args:
            score: Score de productivité [0-100]
        
        Returns:
            Grade: "A", "B", "C", "D", "F"
        """
        if score >= 90:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    @staticmethod
    def should_create_alert(event_type: str, severity: str) -> bool:
        """Déterminer si un événement doit créer une alerte"""
        critical_events = [
            "machine_stopped",
            "employee_absent",
            "production_low",
            "anomaly_detected"
        ]
        
        return event_type in critical_events or severity in ["warning", "critical"]
    
    @staticmethod
    def get_alert_priority(severity: str) -> int:
        """
        Obtenir la priorité d'une alerte
        
        Returns:
            1 = Critique, 2 = Moyenne, 3 = Basse
        """
        priority_map = {
            "critical": 1,
            "high": 1,
            "warning": 2,
            "medium": 2,
            "info": 3,
            "low": 3
        }
        
        return priority_map.get(severity, 3)