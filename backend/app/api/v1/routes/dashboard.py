#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour le dashboard
Vue d'ensemble consolidée
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, date

from app.services.analytics import ProductivityService
from core.database import Database

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview():
    """
    Obtenir une vue d'ensemble complète du dashboard
    
    Returns:
        Vue d'ensemble consolidée
    """
    try:
        # KPIs temps réel
        realtime_metrics = await KPIService.get_realtime_metrics()
        
        # Résumé machines
        machines_summary = await KPIService.get_machines_status_summary()
        
        # Employés
        employees_collection = Database.get_collection("employees")
        total_employees = await employees_collection.count_documents({"is_active": True})
        
        # Vidéos du jour
        videos_collection = Database.get_collection("video_uploads")
        today_start = datetime.combine(date.today(), datetime.min.time())
        videos_today = await videos_collection.count_documents({
            "processed_at": {"$gte": today_start},
            "status": "completed"
        })
        
        # Alertes actives
        alerts_collection = Database.get_collection("alerts")
        active_alerts = await alerts_collection.count_documents({"is_resolved": False})
        
        return {
            "timestamp": datetime.now(),
            "realtime": realtime_metrics,
            "summary": {
                "employees": {
                    "total": total_employees,
                    "present": realtime_metrics.get("metrics", {}).get("employees_present", 0) if realtime_metrics.get("status") == "active" else 0
                },
                "machines": {
                    "total": machines_summary["total"],
                    "active": machines_summary["active"],
                    "stopped": machines_summary["stopped"]
                },
                "videos_processed_today": videos_today,
                "active_alerts": active_alerts
            },
            "machines_detail": machines_summary["machines"]
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur vue d'ensemble dashboard : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/productivity/current")
async def get_current_productivity():
    """
    Obtenir la productivité actuelle
    (Basée sur la dernière vidéo traitée)
    
    Returns:
        Métriques de productivité
    """
    try:
        # Récupérer la dernière vidéo complète
        videos_collection = Database.get_collection("video_uploads")
        latest_video = await videos_collection.find_one(
            {"status": "completed"},
            sort=[("processed_at", -1)]
        )
        
        if not latest_video:
            return {
                "status": "no_data",
                "message": "Aucune vidéo traitée disponible"
            }
        
        video_id = str(latest_video["_id"])
        
        # Calculer la productivité
        productivity = await ProductivityService.calculate_from_video(video_id)
        
        return productivity
    
    except Exception as e:
        logger.error(f"❌ Erreur productivité actuelle : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/active")
async def get_active_alerts():
    """
    Obtenir les alertes actives
    
    Returns:
        Liste des alertes non résolues
    """
    try:
        collection = Database.get_collection("alerts")
        cursor = collection.find({"is_resolved": False}).sort("created_at", -1).limit(20)
        alerts = await cursor.to_list(length=20)
        
        return {
            "count": len(alerts),
            "alerts": [
                {
                    "id": str(alert["_id"]),
                    "type": alert["alert_type"],
                    "severity": alert["severity"],
                    "message": alert["message"],
                    "created_at": alert["created_at"]
                }
                for alert in alerts
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur alertes actives : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/today")
async def get_today_stats():
    """
    Obtenir les statistiques du jour
    
    Returns:
        Statistiques de la journée
    """
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        
        # Vidéos traitées
        videos_collection = Database.get_collection("video_uploads")
        videos_cursor = videos_collection.find({
            "processed_at": {"$gte": today_start},
            "status": "completed"
        })
        videos = await videos_cursor.to_list(length=None)
        
        total_detections = sum(v.get("total_detections", 0) for v in videos)
        
        # Événements créés
        events_collection = Database.get_collection("events")
        events_today = await events_collection.count_documents({
            "created_at": {"$gte": today_start}
        })
        
        return {
            "date": date.today(),
            "videos_processed": len(videos),
            "total_detections": total_detections,
            "events_generated": events_today
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur stats du jour : {e}")
        raise HTTPException(status_code=500, detail=str(e))