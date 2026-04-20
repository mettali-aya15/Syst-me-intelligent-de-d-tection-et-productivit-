#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les KPIs
Snapshots horaires, rapports journaliers, métriques dashboard
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime, timedelta
from typing import Optional

from app.services.analytics import KPICalculator
from app.services.reports import DailyReportGenerator

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/snapshots/generate")
async def generate_kpi_snapshot(
    video_id: str,
    target_date: Optional[date] = None,
    target_hour: Optional[int] = None
):
    """
    Générer un snapshot KPI horaire
    
    - **video_id**: ID de la vidéo analysée
    - **target_date**: Date cible (défaut: aujourd'hui)
    - **target_hour**: Heure cible (défaut: heure actuelle)
    
    Returns:
        KPI Snapshot créé
    """
    try:
        snapshot = await KPICalculator.generate_hourly_snapshot(
            video_id=video_id,
            target_date=target_date,
            target_hour=target_hour
        )
        
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail="Impossible de générer le snapshot (aucune détection trouvée)"
            )
        
        return {
            "id": str(snapshot.id),
            "date": snapshot.date,
            "hour": snapshot.hour,
            "employees": snapshot.employees.dict(),
            "machines": snapshot.machines.dict(),
            "tables": snapshot.tables.dict(),
            "production": snapshot.production.dict(),
            "productivity_rate": snapshot.productivity_rate
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur génération snapshot : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_kpis(days: int = Query(7, ge=1, le=30)):
    """
    Obtenir les KPIs pour le dashboard
    
    - **days**: Nombre de jours à analyser
    
    Returns:
        KPIs du dashboard
    """
    try:
        kpis = await KPICalculator.get_dashboard_kpis(date_range=days)
        
        return kpis
    
    except Exception as e:
        logger.error(f"❌ Erreur KPIs dashboard : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime")
async def get_realtime_metrics():
    """
    Obtenir les métriques en temps réel
    
    Returns:
        Métriques temps réel
    """
    try:
        metrics = await KPICalculator.get_realtime_metrics()
        
        return metrics
    
    except Exception as e:
        logger.error(f"❌ Erreur métriques temps réel : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/daily/generate")
async def generate_daily_report(target_date: Optional[date] = None):
    """
    Générer un rapport journalier
    
    - **target_date**: Date du rapport (défaut: aujourd'hui)
    
    Returns:
        Rapport journalier
    """
    try:
        report = await DailyReportGenerator.generate_report(target_date)
        
        return {
            "id": str(report.id),
            "date": report.date,
            "summary": report.summary,
            "employees_present": report.employees_present,
            "employees_absent": report.employees_absent,
            "total_videos_processed": report.total_videos_processed,
            "total_detections": report.total_detections,
            "productivity_score": report.productivity_score,
            "generated_at": report.generated_at
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/weekly")
async def get_weekly_summary(end_date: Optional[date] = None):
    """
    Obtenir le résumé hebdomadaire
    
    - **end_date**: Date de fin (défaut: aujourd'hui)
    
    Returns:
        Résumé de la semaine
    """
    try:
        summary = await DailyReportGenerator.get_weekly_summary(end_date)
        
        return summary
    
    except Exception as e:
        logger.error(f"❌ Erreur résumé hebdomadaire : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/monthly")
async def get_monthly_summary(
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """
    Obtenir le résumé mensuel
    
    - **year**: Année (défaut: année actuelle)
    - **month**: Mois (défaut: mois actuel)
    
    Returns:
        Résumé du mois
    """
    try:
        summary = await DailyReportGenerator.get_monthly_summary(year, month)
        
        return summary
    
    except Exception as e:
        logger.error(f"❌ Erreur résumé mensuel : {e}")
        raise HTTPException(status_code=500, detail=str(e))