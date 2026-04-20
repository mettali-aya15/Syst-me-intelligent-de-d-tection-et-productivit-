#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculateur de KPIs (Key Performance Indicators)
Génère des snapshots horaires et rapports journaliers
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from bson import ObjectId

from app.models.kpi import (
    KPISnapshot, 
    DailyReport,
    EmployeeMetrics,
    MachineMetrics,
    TableMetrics,
    ProductionMetrics
)
from core.database import Database

import logging
logger = logging.getLogger(__name__)


class KPICalculator:
    """Calculateur de KPIs pour le dashboard"""
    
    @staticmethod
    async def generate_hourly_snapshot(
        video_id: str,
        target_date: date = None,
        target_hour: int = None
    ) -> KPISnapshot:
        """
        Générer un snapshot KPI horaire à partir d'une vidéo
        
        Args:
            video_id: ID de la vidéo analysée
            target_date: Date cible (défaut: aujourd'hui)
            target_hour: Heure cible (défaut: heure actuelle)
        
        Returns:
            KPISnapshot créé
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        if target_hour is None:
            target_hour = datetime.now().hour
        
        try:
            # Récupérer les détections de la vidéo
            detections_collection = Database.get_collection("video_detections")
            cursor = detections_collection.find({"video_id": ObjectId(video_id)})
            detections = await cursor.to_list(length=None)
            
            if not detections:
                logger.warning(f"⚠️ Aucune détection pour vidéo {video_id}")
                return None
            
            # Analyser les détections
            employees_set = set()
            temp_count = 0
            unidentified_count = 0
            
            machines_set = set()
            machines_active = set()
            
            tables_set = set()
            tables_occupied = set()
            
            products_count = 0
            
            for det in detections:
                class_name = det["class_name"]
                source = det["source"]
                
                # EMPLOYÉS
                if source == "employees":
                    if class_name == "temp":
                        temp_count += 1
                    elif class_name == "employe":
                        unidentified_count += 1
                    else:
                        # Employé permanent nommé
                        employees_set.add(class_name)
                
                # MACHINES
                elif "machine" in class_name.lower():
                    machines_set.add(class_name)
                    machines_active.add(class_name)
                
                # TABLES
                elif "table" in class_name.lower():
                    tables_set.add(class_name)
                    tables_occupied.add(class_name)
                
                # PRODUITS
                elif "produit" in class_name.lower() or "product" in class_name.lower():
                    products_count += 1
            
            # Construire les métriques
            employee_metrics = EmployeeMetrics(
                total=len(employees_set) + (1 if temp_count > 0 else 0) + (1 if unidentified_count > 0 else 0),
                present=len(employees_set),
                absent=0,  # À calculer avec référence aux employés enregistrés
                temp_workers=1 if temp_count > 0 else 0
            )
            
            machine_metrics = MachineMetrics(
                total=len(machines_set),
                active=len(machines_active),
                stopped=0,
                in_maintenance=0
            )
            
            table_metrics = TableMetrics(
                total=len(tables_set),
                occupied=len(tables_occupied),
                free=len(tables_set) - len(tables_occupied)
            )
            
            production_metrics = ProductionMetrics(
                total_produced=products_count,
                hourly_rate=products_count  # Estimation
            )
            
            # Calculer productivité
            productivity_rate = KPICalculator._calculate_productivity_rate(
                employees=employee_metrics,
                machines=machine_metrics,
                production=production_metrics
            )
            
            # Créer le snapshot
            snapshot = KPISnapshot(
                date=target_date,
                hour=target_hour,
                employees=employee_metrics,
                machines=machine_metrics,
                tables=table_metrics,
                production=production_metrics,
                productivity_rate=productivity_rate,
                video_ids=[str(video_id)]
            )
            
            # Sauvegarder en DB
            collection = Database.get_collection("kpi_snapshots")
            snapshot_dict = snapshot.dict(by_alias=True, exclude={"id"})
            result = await collection.insert_one(snapshot_dict)
            
            snapshot.id = result.inserted_id
            
            logger.info(f"✅ Snapshot KPI créé : {target_date} {target_hour}h")
            
            return snapshot
        
        except Exception as e:
            logger.error(f"❌ Erreur génération snapshot : {e}")
            raise
    
    @staticmethod
    def _calculate_productivity_rate(
        employees: EmployeeMetrics,
        machines: MachineMetrics,
        production: ProductionMetrics
    ) -> float:
        """
        Calculer le taux de productivité global [0-100]
        
        Formule :
        - Présence employés : 30%
        - Machines actives : 40%
        - Production : 30%
        """
        # Employés présents (sur base de 5 employés max)
        employee_score = min(employees.present / 5, 1.0) * 30
        
        # Machines actives (sur base de 3 machines max)
        machine_score = 0
        if machines.total > 0:
            machine_score = (machines.active / machines.total) * 40
        
        # Production (sur base de 50 produits/heure)
        production_score = min(production.total_produced / 50, 1.0) * 30
        
        total_score = employee_score + machine_score + production_score
        
        return round(total_score, 2)
    
    @staticmethod
    async def generate_daily_report(target_date: date = None) -> DailyReport:
        """
        Générer un rapport journalier consolidé
        
        Args:
            target_date: Date cible (défaut: aujourd'hui)
        
        Returns:
            DailyReport créé
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        try:
            # Récupérer tous les snapshots de la journée
            snapshots_collection = Database.get_collection("kpi_snapshots")
            cursor = snapshots_collection.find({"date": target_date})
            snapshots = await cursor.to_list(length=None)
            
            # Récupérer toutes les vidéos du jour
            videos_collection = Database.get_collection("video_uploads")
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            
            videos_cursor = videos_collection.find({
                "processed_at": {
                    "$gte": start_datetime,
                    "$lt": end_datetime
                },
                "status": "completed"
            })
            videos = await videos_cursor.to_list(length=None)
            
            # Agréger les métriques
            total_detections = sum(v.get("total_detections", 0) for v in videos)
            
            # Récupérer tous les employés enregistrés
            employees_collection = Database.get_collection("employees")
            all_employees = await employees_collection.find({"is_active": True}).to_list(length=None)
            
            # Déterminer présences/absences
            employees_detected = set()
            for v in videos:
                summary = v.get("summary", {})
                for class_name in summary.keys():
                    # Vérifier si c'est un nom d'employé
                    if any(emp["name"] == class_name for emp in all_employees):
                        employees_detected.add(class_name)
            
            employees_present = list(employees_detected)
            employees_absent = [
                emp["name"] for emp in all_employees 
                if emp["name"] not in employees_detected
            ]
            
            # Calculer temps d'arrêt machines (simulation)
            machines_downtime_minutes = 0
            
            # Score de productivité moyen
            avg_productivity = 0
            if snapshots:
                avg_productivity = sum(s.get("productivity_rate", 0) for s in snapshots) / len(snapshots)
            
            # Créer le rapport
            report = DailyReport(
                date=target_date,
                summary={
                    "total_videos": len(videos),
                    "total_detections": total_detections,
                    "employees_present_count": len(employees_present),
                    "employees_absent_count": len(employees_absent),
                    "avg_productivity": round(avg_productivity, 2)
                },
                employees_present=employees_present,
                employees_absent=employees_absent,
                total_videos_processed=len(videos),
                total_detections=total_detections,
                machines_downtime_minutes=machines_downtime_minutes,
                productivity_score=round(avg_productivity, 2),
                hourly_snapshots=[ObjectId(s["_id"]) for s in snapshots]
            )
            
            # Sauvegarder en DB
            reports_collection = Database.get_collection("daily_reports")
            report_dict = report.dict(by_alias=True, exclude={"id"})
            result = await reports_collection.insert_one(report_dict)
            
            report.id = result.inserted_id
            
            logger.info(f"✅ Rapport journalier créé : {target_date}")
            
            return report
        
        except Exception as e:
            logger.error(f"❌ Erreur génération rapport : {e}")
            raise
    
    @staticmethod
    async def get_dashboard_kpis(date_range: int = 7) -> Dict:
        """
        Obtenir les KPIs pour le dashboard
        
        Args:
            date_range: Nombre de jours à analyser (défaut: 7)
        
        Returns:
            KPIs formatés pour le dashboard
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=date_range)
            
            # KPIs aujourd'hui
            today_snapshots = await Database.get_collection("kpi_snapshots").find({
                "date": end_date
            }).to_list(length=None)
            
            latest_snapshot = None
            if today_snapshots:
                latest_snapshot = max(today_snapshots, key=lambda x: x.get("hour", 0))
            
            # Rapport du jour
            today_report = await Database.get_collection("daily_reports").find_one({
                "date": end_date
            })
            
            # Tendances sur la période
            reports_cursor = Database.get_collection("daily_reports").find({
                "date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
            reports = await reports_cursor.to_list(length=None)
            
            # Calculer tendances
            productivity_trend = []
            for report in sorted(reports, key=lambda x: x["date"]):
                productivity_trend.append({
                    "date": report["date"].isoformat(),
                    "score": report.get("productivity_score", 0)
                })
            
            return {
                "current": {
                    "date": end_date.isoformat(),
                    "employees": latest_snapshot.get("employees") if latest_snapshot else None,
                    "machines": latest_snapshot.get("machines") if latest_snapshot else None,
                    "tables": latest_snapshot.get("tables") if latest_snapshot else None,
                    "productivity_rate": latest_snapshot.get("productivity_rate", 0) if latest_snapshot else 0
                },
                "today": {
                    "total_videos": today_report.get("total_videos_processed", 0) if today_report else 0,
                    "total_detections": today_report.get("total_detections", 0) if today_report else 0,
                    "employees_present": today_report.get("employees_present", []) if today_report else [],
                    "employees_absent": today_report.get("employees_absent", []) if today_report else [],
                    "productivity_score": today_report.get("productivity_score", 0) if today_report else 0
                },
                "trends": {
                    "period_days": date_range,
                    "productivity": productivity_trend
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur KPIs dashboard : {e}")
            raise
    
    @staticmethod
    async def get_realtime_metrics() -> Dict:
        """
        Obtenir les métriques en temps réel
        (Basées sur la dernière vidéo traitée)
        """
        try:
            # Récupérer la dernière vidéo traitée
            videos_collection = Database.get_collection("video_uploads")
            latest_video = await videos_collection.find_one(
                {"status": "completed"},
                sort=[("processed_at", -1)]
            )
            
            if not latest_video:
                return {
                    "status": "no_data",
                    "message": "Aucune vidéo traitée récemment"
                }
            
            video_id = latest_video["_id"]
            
            # Récupérer les détections
            detections_collection = Database.get_collection("video_detections")
            cursor = detections_collection.find({"video_id": video_id})
            detections = await cursor.to_list(length=None)
            
            # Compter par catégorie
            employees_detected = set()
            machines_active = set()
            tables_occupied = set()
            
            for det in detections:
                class_name = det["class_name"]
                source = det["source"]
                
                if source == "employees" and class_name not in ["temp", "employe"]:
                    employees_detected.add(class_name)
                elif "machine" in class_name.lower():
                    machines_active.add(class_name)
                elif "table" in class_name.lower():
                    tables_occupied.add(class_name)
            
            return {
                "status": "active",
                "last_update": latest_video.get("processed_at"),
                "video_id": str(video_id),
                "metrics": {
                    "employees_present": len(employees_detected),
                    "employees_list": list(employees_detected),
                    "machines_active": len(machines_active),
                    "machines_list": list(machines_active),
                    "tables_occupied": len(tables_occupied),
                    "total_detections": len(detections)
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur métriques temps réel : {e}")
            raise