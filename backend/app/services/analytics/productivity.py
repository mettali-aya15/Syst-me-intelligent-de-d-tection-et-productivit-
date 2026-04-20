#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de calcul de productivité
Extrapolation : vidéo courte → heure → journée
"""

from typing import Dict, List
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.detection import FrameDetection
from core.database import Database
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


class ProductivityService:
    """
    Calcule la productivité à partir de détections vidéo
    Extrapolation : 2min de vidéo → 1h → 8h (journée)
    """
    
    @staticmethod
    async def calculate_from_video(
        video_id: str,
        work_hours_per_day: int = None
    ) -> Dict:
        """
        Calculer la productivité à partir d'une vidéo
        
        Args:
            video_id: ID de la vidéo
            work_hours_per_day: Heures de travail par jour (défaut: 8)
        
        Returns:
            Métriques de productivité extrapolées
        """
        if work_hours_per_day is None:
            work_hours_per_day = settings.WORK_HOURS_PER_DAY
        
        try:
            # Récupérer la vidéo
            videos_collection = Database.get_collection("video_uploads")
            video_doc = await videos_collection.find_one({"_id": ObjectId(video_id)})
            
            if not video_doc:
                raise ValueError(f"Vidéo introuvable : {video_id}")
            
            video_duration = video_doc["duration"]  # En secondes
            video_duration_minutes = video_duration / 60
            
            # Récupérer les détections
            detections_collection = Database.get_collection("video_detections")
            cursor = detections_collection.find({"video_id": ObjectId(video_id)})
            detections = await cursor.to_list(length=None)
            
            logger.info(f"📊 Analyse de {len(detections)} détections sur {video_duration_minutes:.2f} min")
            
            # Compter par classe
            class_counts = {}
            employees_present = set()
            temp_workers = 0
            unidentified_employees = 0
            machines_active = set()
            tables_occupied = set()
            
            for det in detections:
                class_name = det["class_name"]
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
                
                # Catégoriser
                if det["source"] == "employees":
                    if class_name == "temp":
                        temp_workers += 1
                    elif class_name == "employe":
                        unidentified_employees += 1
                    else:
                        # Employé permanent
                        employees_present.add(class_name)
                
                elif "machine" in class_name.lower():
                    machines_active.add(class_name)
                
                elif "table" in class_name.lower():
                    tables_occupied.add(class_name)
            
            # Métriques de la période vidéo
            period_metrics = {
                "duration_minutes": video_duration_minutes,
                "employees": {
                    "permanent": len(employees_present),
                    "temp": temp_workers,
                    "unidentified": unidentified_employees,
                    "total": len(employees_present) + (temp_workers > 0) + (unidentified_employees > 0)
                },
                "machines": {
                    "active_count": len(machines_active),
                    "list": list(machines_active)
                },
                "tables": {
                    "occupied_count": len(tables_occupied),
                    "list": list(tables_occupied)
                },
                "detections_total": len(detections),
                "detections_by_class": class_counts
            }
            
            # EXTRAPOLATION HORAIRE
            minutes_per_hour = 60
            extrapolation_factor_hour = minutes_per_hour / video_duration_minutes
            
            hourly_metrics = {
                "estimated_detections": int(len(detections) * extrapolation_factor_hour),
                "employees": period_metrics["employees"].copy(),  # Même nombre d'employés
                "machines": {
                    "active_count": period_metrics["machines"]["active_count"],
                    "estimated_production": int(class_counts.get("produit", 0) * extrapolation_factor_hour)
                },
                "tables": {
                    "occupied_count": period_metrics["tables"]["occupied_count"],
                    "estimated_turnover": int(len(tables_occupied) * extrapolation_factor_hour * 0.5)  # 50% rotation
                }
            }
            
            # EXTRAPOLATION JOURNALIÈRE
            extrapolation_factor_day = (work_hours_per_day * 60) / video_duration_minutes
            
            daily_metrics = {
                "work_hours": work_hours_per_day,
                "estimated_detections": int(len(detections) * extrapolation_factor_day),
                "employees": period_metrics["employees"].copy(),
                "machines": {
                    "active_count": period_metrics["machines"]["active_count"],
                    "estimated_production": int(class_counts.get("produit", 0) * extrapolation_factor_day)
                },
                "tables": {
                    "occupied_count": period_metrics["tables"]["occupied_count"],
                    "estimated_customers": int(len(tables_occupied) * extrapolation_factor_day * 2)  # 2 rotations/heure
                }
            }
            
            # CALCUL DE PRODUCTIVITÉ
            productivity_score = ProductivityService._calculate_productivity_score(
                employees_count=period_metrics["employees"]["total"],
                machines_count=period_metrics["machines"]["active_count"],
                detections_count=len(detections),
                duration_minutes=video_duration_minutes
            )
            
            return {
                "video_id": video_id,
                "analysis_date": datetime.now(),
                "period": period_metrics,
                "hourly": hourly_metrics,
                "daily": daily_metrics,
                "productivity_score": productivity_score,
                "extrapolation_note": f"Basé sur {video_duration_minutes:.2f} min de vidéo"
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur calcul productivité : {e}")
            raise
    
    @staticmethod
    def _calculate_productivity_score(
        employees_count: int,
        machines_count: int,
        detections_count: int,
        duration_minutes: float
    ) -> float:
        """
        Calculer un score de productivité [0-100]
        
        Formule simplifiée :
        - Présence employés : 40%
        - Activité machines : 30%
        - Taux de détection : 30%
        """
        # Normaliser les métriques
        employee_score = min(employees_count / 5, 1.0) * 40  # Max 5 employés = 100%
        machine_score = min(machines_count / 3, 1.0) * 30    # Max 3 machines = 100%
        
        # Taux de détection par minute
        detections_per_minute = detections_count / duration_minutes if duration_minutes > 0 else 0
        detection_score = min(detections_per_minute / 50, 1.0) * 30  # Max 50 détections/min = 100%
        
        total_score = employee_score + machine_score + detection_score
        
        return round(total_score, 2)
    
    @staticmethod
    async def get_daily_productivity(date: datetime.date = None) -> Dict:
        """
        Obtenir la productivité d'une journée complète
        (Agrégation de toutes les vidéos du jour)
        """
        if date is None:
            date = datetime.now().date()
        
        # Récupérer toutes les vidéos du jour
        videos_collection = Database.get_collection("video_uploads")
        
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        cursor = videos_collection.find({
            "processed_at": {
                "$gte": start_date,
                "$lt": end_date
            },
            "status": "completed"
        })
        
        videos = await cursor.to_list(length=None)
        
        if not videos:
            return {
                "date": date,
                "videos_count": 0,
                "message": "Aucune vidéo traitée ce jour"
            }
        
        # Agréger les métriques
        total_detections = sum(v.get("total_detections", 0) for v in videos)
        
        all_summaries = {}
        for v in videos:
            summary = v.get("summary", {})
            for class_name, count in summary.items():
                all_summaries[class_name] = all_summaries.get(class_name, 0) + count
        
        return {
            "date": date,
            "videos_count": len(videos),
            "total_detections": total_detections,
            "summary": all_summaries
        }