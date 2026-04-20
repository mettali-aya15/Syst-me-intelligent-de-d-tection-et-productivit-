#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logique métier pour les machines
Gestion du cycle de vie, détection d'anomalies, calcul de disponibilité
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.machine import Machine, MachineCreate, MachineUpdate
from app.models.detection import FrameDetection
from core.database import Database
from .rules import BusinessRules

import logging
logger = logging.getLogger(__name__)


class MachineLogic:
    """Logique métier pour les machines"""
    
    @staticmethod
    async def create_machine(machine_data: MachineCreate) -> Machine:
        """
        Créer une nouvelle machine
        
        Args:
            machine_data: Données de la machine
        
        Returns:
            Machine créée
        """
        try:
            machine = Machine(**machine_data.dict())
            
            collection = Database.get_collection("machines")
            machine_dict = machine.dict(by_alias=True, exclude={"id"})
            result = await collection.insert_one(machine_dict)
            
            machine.id = result.inserted_id
            
            logger.info(f"✅ Machine créée : {machine.name}")
            
            return machine
        
        except Exception as e:
            logger.error(f"❌ Erreur création machine : {e}")
            raise
    
    @staticmethod
    async def update_machine(machine_id: str, update_data: MachineUpdate) -> Optional[Machine]:
        """
        Mettre à jour une machine
        
        Args:
            machine_id: ID de la machine
            update_data: Données à mettre à jour
        
        Returns:
            Machine mise à jour ou None
        """
        try:
            collection = Database.get_collection("machines")
            
            # Préparer les données à mettre à jour
            update_dict = {
                k: v for k, v in update_data.dict(exclude_unset=True).items() 
                if v is not None
            }
            
            if not update_dict:
                return None
            
            update_dict["updated_at"] = datetime.now()
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(machine_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                logger.info(f"✅ Machine mise à jour : {machine_id}")
                return Machine(**result)
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour machine : {e}")
            raise
    
    @staticmethod
    async def get_machine_by_name(name: str) -> Optional[Machine]:
        """
        Récupérer une machine par son nom
        
        Args:
            name: Nom de la machine
        
        Returns:
            Machine ou None
        """
        collection = Database.get_collection("machines")
        machine_doc = await collection.find_one({"name": name})
        
        return Machine(**machine_doc) if machine_doc else None
    
    @staticmethod
    async def update_machine_activity(
        machine_name: str,
        video_id: str,
        activity_detected: bool
    ) -> bool:
        """
        Mettre à jour l'activité d'une machine basée sur détection
        
        Args:
            machine_name: Nom de la machine
            video_id: ID de la vidéo source
            activity_detected: True si machine active détectée
        
        Returns:
            True si mise à jour réussie
        """
        try:
            machine = await MachineLogic.get_machine_by_name(machine_name)
            
            if not machine:
                # Créer la machine si elle n'existe pas
                machine_data = MachineCreate(
                    name=machine_name,
                    type="unknown",  # À déterminer
                    zone="unknown",
                    status="active" if activity_detected else "stopped"
                )
                await MachineLogic.create_machine(machine_data)
                return True
            
            # Mettre à jour le statut
            new_status = "active" if activity_detected else "stopped"
            
            update_data = MachineUpdate(
                status=new_status,
                last_activity=datetime.now() if activity_detected else None
            )
            
            await MachineLogic.update_machine(str(machine.id), update_data)
            
            logger.info(f"✅ Activité machine mise à jour : {machine_name} -> {new_status}")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour activité : {e}")
            return False
    
    @staticmethod
    async def calculate_machine_availability(
        machine_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Calculer la disponibilité d'une machine sur une période
        
        Disponibilité = (Temps actif / Temps total) * 100
        
        Args:
            machine_id: ID de la machine
            start_date: Date de début
            end_date: Date de fin
        
        Returns:
            Métriques de disponibilité
        """
        try:
            # Récupérer toutes les détections de la machine sur la période
            detections_collection = Database.get_collection("video_detections")
            
            machine = await Database.get_collection("machines").find_one(
                {"_id": ObjectId(machine_id)}
            )
            
            if not machine:
                return {"error": "Machine introuvable"}
            
            machine_name = machine["name"]
            
            # Récupérer les vidéos de la période
            videos_collection = Database.get_collection("video_uploads")
            videos_cursor = videos_collection.find({
                "processed_at": {
                    "$gte": start_date,
                    "$lte": end_date
                },
                "status": "completed"
            })
            
            videos = await videos_cursor.to_list(length=None)
            
            if not videos:
                return {
                    "machine_id": machine_id,
                    "machine_name": machine_name,
                    "period_start": start_date,
                    "period_end": end_date,
                    "availability_rate": 0,
                    "total_active_seconds": 0,
                    "total_period_seconds": 0,
                    "message": "Aucune vidéo sur cette période"
                }
            
            total_active_frames = 0
            total_frames = 0
            
            for video in videos:
                video_id = video["_id"]
                video_fps = video.get("fps", 30)
                video_total_frames = video.get("total_frames", 0)
                
                # Compter les détections de cette machine
                detections_cursor = detections_collection.find({
                    "video_id": video_id,
                    "class_name": machine_name
                })
                
                detections = await detections_cursor.to_list(length=None)
                
                active_frames = len(detections)
                
                total_active_frames += active_frames
                total_frames += video_total_frames
            
            # Calculer la disponibilité
            availability_rate = (total_active_frames / total_frames * 100) if total_frames > 0 else 0
            
            # Convertir en secondes (approximation)
            avg_fps = sum(v.get("fps", 30) for v in videos) / len(videos)
            total_active_seconds = total_active_frames / avg_fps if avg_fps > 0 else 0
            total_period_seconds = total_frames / avg_fps if avg_fps > 0 else 0
            
            return {
                "machine_id": machine_id,
                "machine_name": machine_name,
                "period_start": start_date,
                "period_end": end_date,
                "availability_rate": round(availability_rate, 2),
                "total_active_seconds": round(total_active_seconds, 2),
                "total_period_seconds": round(total_period_seconds, 2),
                "total_active_minutes": round(total_active_seconds / 60, 2),
                "downtime_minutes": round((total_period_seconds - total_active_seconds) / 60, 2),
                "videos_analyzed": len(videos)
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur calcul disponibilité : {e}")
            raise
    
    @staticmethod
    async def detect_machine_anomalies(
        machine_id: str,
        frames_detections: List[FrameDetection],
        video_duration: float
    ) -> List[Dict]:
        """
        Détecter les anomalies d'une machine dans une vidéo
        
        Args:
            machine_id: ID de la machine
            frames_detections: Détections de la vidéo
            video_duration: Durée de la vidéo en secondes
        
        Returns:
            Liste d'anomalies détectées
        """
        try:
            anomalies = []
            
            machine = await Database.get_collection("machines").find_one(
                {"_id": ObjectId(machine_id)}
            )
            
            if not machine:
                return anomalies
            
            machine_name = machine["name"]
            
            # Compter les apparitions de la machine
            machine_frames = []
            total_frames = len(frames_detections)
            
            for fd in frames_detections:
                for det in fd.detections:
                    if det.class_name == machine_name:
                        machine_frames.append(fd.frame_number)
            
            if not machine_frames:
                # Machine jamais détectée = arrêt total
                anomalies.append({
                    "type": "complete_stoppage",
                    "severity": "critical",
                    "message": f"Machine {machine_name} jamais détectée dans la vidéo",
                    "duration_minutes": video_duration / 60
                })
                return anomalies
            
            # Calculer le taux d'activité
            activity_rate = len(machine_frames) / total_frames if total_frames > 0 else 0
            
            # ANOMALIE 1 : Faible taux d'activité
            if activity_rate < 0.3:  # Moins de 30% d'activité
                downtime_minutes = video_duration * (1 - activity_rate) / 60
                
                severity = "critical" if activity_rate < 0.1 else "warning"
                
                anomalies.append({
                    "type": "low_activity",
                    "severity": severity,
                    "message": f"Faible activité machine : {activity_rate*100:.1f}%",
                    "activity_rate": round(activity_rate, 3),
                    "downtime_minutes": round(downtime_minutes, 2)
                })
            
            # ANOMALIE 2 : Longues périodes d'inactivité
            sorted_frames = sorted(machine_frames)
            max_gap = 0
            max_gap_start = 0
            
            for i in range(1, len(sorted_frames)):
                gap = sorted_frames[i] - sorted_frames[i-1]
                if gap > max_gap:
                    max_gap = gap
                    max_gap_start = sorted_frames[i-1]
            
            # Si gap > 5 minutes (approx 150 frames à 30fps)
            if max_gap > 150:
                gap_minutes = max_gap / 30  # Approximation
                
                if BusinessRules.is_critical_machine_downtime(gap_minutes):
                    anomalies.append({
                        "type": "prolonged_stoppage",
                        "severity": "critical",
                        "message": f"Arrêt prolongé détecté : {gap_minutes:.1f} minutes",
                        "gap_frames": max_gap,
                        "gap_minutes": round(gap_minutes, 2),
                        "start_frame": max_gap_start
                    })
            
            # ANOMALIE 3 : Activité intermittente (beaucoup de démarrages/arrêts)
            start_stop_count = 0
            for i in range(1, len(sorted_frames)):
                gap = sorted_frames[i] - sorted_frames[i-1]
                if gap > 30:  # Gap de plus de 1 seconde
                    start_stop_count += 1
            
            if start_stop_count > 10:  # Plus de 10 démarrages/arrêts
                anomalies.append({
                    "type": "intermittent_activity",
                    "severity": "warning",
                    "message": f"Activité intermittente : {start_stop_count} cycles démarrage/arrêt",
                    "cycle_count": start_stop_count
                })
            
            return anomalies
        
        except Exception as e:
            logger.error(f"❌ Erreur détection anomalies : {e}")
            raise
    
    @staticmethod
    async def get_machines_status_summary() -> Dict:
        """
        Obtenir un résumé du statut de toutes les machines
        
        Returns:
            Résumé des machines
        """
        try:
            collection = Database.get_collection("machines")
            machines = await collection.find().to_list(length=None)
            
            summary = {
                "total": len(machines),
                "active": 0,
                "stopped": 0,
                "maintenance": 0,
                "unknown": 0,
                "machines": []
            }
            
            for machine_doc in machines:
                machine = Machine(**machine_doc)
                status = machine.status
                
                # Compter par statut
                if status == "active":
                    summary["active"] += 1
                elif status == "stopped":
                    summary["stopped"] += 1
                elif status == "maintenance":
                    summary["maintenance"] += 1
                else:
                    summary["unknown"] += 1
                
                # Ajouter aux détails
                summary["machines"].append({
                    "id": str(machine.id),
                    "name": machine.name,
                    "type": machine.type,
                    "zone": machine.zone,
                    "status": status,
                    "last_activity": machine.last_activity
                })
            
            return summary
        
        except Exception as e:
            logger.error(f"❌ Erreur résumé machines : {e}")
            raise
    
    @staticmethod
    async def predict_maintenance_need(machine_id: str) -> Dict:
        """
        Prédire le besoin de maintenance basé sur l'historique
        (Logique simplifiée - peut être améliorée avec ML)
        
        Args:
            machine_id: ID de la machine
        
        Returns:
            Prédiction de maintenance
        """
        try:
            # Calculer la disponibilité sur les 7 derniers jours
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            availability = await MachineLogic.calculate_machine_availability(
                machine_id, start_date, end_date
            )
            
            if "error" in availability:
                return availability
            
            availability_rate = availability["availability_rate"]
            
            # Règles simples de prédiction
            if availability_rate < 50:
                maintenance_priority = "urgent"
                recommendation = "Maintenance immédiate recommandée"
            elif availability_rate < 70:
                maintenance_priority = "high"
                recommendation = "Planifier maintenance sous 3 jours"
            elif availability_rate < 85:
                maintenance_priority = "medium"
                recommendation = "Planifier maintenance sous 1 semaine"
            else:
                maintenance_priority = "low"
                recommendation = "Aucune maintenance urgente nécessaire"
            
            return {
                "machine_id": machine_id,
                "machine_name": availability["machine_name"],
                "availability_rate_7days": availability_rate,
                "maintenance_priority": maintenance_priority,
                "recommendation": recommendation,
                "last_7_days_downtime_minutes": availability["downtime_minutes"]
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur prédiction maintenance : {e}")
            raise