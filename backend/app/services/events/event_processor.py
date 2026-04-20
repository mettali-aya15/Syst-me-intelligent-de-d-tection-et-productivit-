#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processeur d'événements
Analyse les détections et génère des événements automatiquement
"""

from typing import List, Dict
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.detection import FrameDetection
from .event_builder import EventBuilder
from core.database import Database

import logging
logger = logging.getLogger(__name__)


class EventProcessor:
    """Processeur d'événements basé sur les détections"""
    
    @staticmethod
    async def process_video_detections(
        video_id: str,
        frames_detections: List[FrameDetection],
        video_duration: float
    ) -> Dict:
        """
        Analyser les détections d'une vidéo et générer des événements
        
        Args:
            video_id: ID de la vidéo
            frames_detections: Liste des détections par frame
            video_duration: Durée de la vidéo en secondes
        
        Returns:
            Résumé des événements créés
        """
        try:
            events_created = {
                "employee_events": [],
                "machine_events": [],
                "production_events": [],
                "anomaly_events": []
            }
            
            # Analyser les employés
            employee_events = await EventProcessor._process_employee_detections(
                video_id, frames_detections
            )
            events_created["employee_events"] = employee_events
            
            # Analyser les machines
            machine_events = await EventProcessor._process_machine_detections(
                video_id, frames_detections, video_duration
            )
            events_created["machine_events"] = machine_events
            
            # Analyser la production
            production_events = await EventProcessor._process_production_detections(
                video_id, frames_detections, video_duration
            )
            events_created["production_events"] = production_events
            
            logger.info(f"✅ Événements générés pour vidéo {video_id}: {sum(len(v) for v in events_created.values())} total")
            
            return events_created
        
        except Exception as e:
            logger.error(f"❌ Erreur traitement événements : {e}")
            raise
    
    @staticmethod
    async def _process_employee_detections(
        video_id: str,
        frames_detections: List[FrameDetection]
    ) -> List:
        """Traiter les détections d'employés"""
        events = []
        
        # Extraire les employés détectés
        detected_employees = set()
        temp_workers_count = 0
        
        for fd in frames_detections:
            for det in fd.detections:
                if det.source == "employees":
                    if det.class_name == "temp":
                        temp_workers_count += 1
                    elif det.class_name != "employe":
                        detected_employees.add(det.class_name)
        
        # Récupérer les employés attendus
        employees_collection = Database.get_collection("employees")
        expected_employees = await employees_collection.find({
            "is_active": True,
            "is_temp": False
        }).to_list(length=None)
        
        expected_names = [emp["name"] for emp in expected_employees]
        
        # Détecter absences
        absence_events = await EventBuilder.detect_employee_absence(
            expected_names, list(detected_employees)
        )
        events.extend(absence_events)
        
        # Détecter travailleurs temporaires
        if temp_workers_count > 0:
            event = await EventBuilder.create_event(
                event_type="temp_worker_detected",
                message=f"Travailleur(s) temporaire(s) détecté(s) : {temp_workers_count} détections",
                severity="info",
                video_id=video_id,
                metadata={"temp_count": temp_workers_count}
            )
            events.append(event)
        
        return events
    
    @staticmethod
    async def _process_machine_detections(
        video_id: str,
        frames_detections: List[FrameDetection],
        video_duration: float
    ) -> List:
        """Traiter les détections de machines"""
        events = []
        
        # Compter les apparitions par machine
        machine_frames = {}
        total_frames = len(frames_detections)
        
        for fd in frames_detections:
            for det in fd.detections:
                if "machine" in det.class_name.lower():
                    machine_frames[det.class_name] = machine_frames.get(det.class_name, 0) + 1
        
        # Détecter machines peu actives
        machines_collection = Database.get_collection("machines")
        
        for machine_name, frame_count in machine_frames.items():
            activity_rate = frame_count / total_frames if total_frames > 0 else 0
            
            # Si machine détectée dans moins de 30% des frames
            if activity_rate < 0.3:
                machine_doc = await machines_collection.find_one({"name": machine_name})
                
                if machine_doc:
                    estimated_downtime = video_duration * (1 - activity_rate) / 60  # En minutes
                    
                    event = await EventBuilder.detect_machine_stoppage(
                        machine_name=machine_name,
                        machine_id=str(machine_doc["_id"]),
                        duration_minutes=estimated_downtime
                    )
                    events.append(event)
        
        return events
    
    @staticmethod
    async def _process_productio