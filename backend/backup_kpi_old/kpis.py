#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les KPI avec périodes dynamiques: heure, jour, semaine, mois
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Literal
from datetime import datetime, timedelta

from app.services.analytics.kpi_service import KPIService
from app.models.kpi import KPIGlobal

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/global/today", response_model=dict)
async def get_kpi_today(
    periode: Literal["heure", "jour", "semaine", "mois"] = Query(
        "jour", 
        description="Type de période: heure (dernière heure), jour (aujourd'hui), semaine (cette semaine), mois (ce mois)"
    )
):
    """
    Obtenir les KPI globaux selon la période choisie
    
    Args:
        periode: Type de période (heure/jour/semaine/mois)
    
    Returns: KPI complets - sections optionnelles selon détections
    """
    try:
        logger.info(f"📊 Requête KPI période: {periode}")
        
        # Calculer les KPI selon la période
        kpi = await KPIService.calculate_kpi_global(periode=periode)
        
        # Convertir en dict avec exclusion des None
        kpi_dict = kpi.model_dump(by_alias=True, exclude_none=True, exclude={"id", "created_at"})
        
        response = {
            "success": True,
            "data": kpi_dict
        }
        
        logger.info(f"✅ KPI {periode} récupérés avec succès")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur KPI {periode} : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global/week", response_model=dict)
async def get_kpi_week():
    """
    Obtenir les KPI globaux de la semaine (alias pour période=semaine)
    
    Returns: KPI de la semaine actuelle
    """
    try:
        logger.info("📊 Requête KPI semaine")
        
        kpi = await KPIService.calculate_kpi_global(periode="semaine")
        
        kpi_dict = kpi.model_dump(by_alias=True, exclude_none=True, exclude={"id", "created_at"})
        
        response = {
            "success": True,
            "data": kpi_dict
        }
        
        logger.info("✅ KPI semaine récupérés avec succès")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur KPI semaine : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global/month", response_model=dict)
async def get_kpi_month():
    """
    Obtenir les KPI globaux du mois (alias pour période=mois)
    
    Returns: KPI du mois actuel
    """
    try:
        logger.info("📊 Requête KPI mois")
        
        kpi = await KPIService.calculate_kpi_global(periode="mois")
        
        kpi_dict = kpi.model_dump(by_alias=True, exclude_none=True, exclude={"id", "created_at"})
        
        response = {
            "success": True,
            "data": kpi_dict
        }
        
        logger.info("✅ KPI mois récupérés avec succès")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur KPI mois : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global/custom", response_model=dict)
async def get_kpi_custom(
    date_debut: datetime = Query(..., description="Date de début"),
    date_fin: datetime = Query(..., description="Date de fin"),
    periode: Literal["heure", "jour", "semaine", "mois"] = Query(
        "jour",
        description="Type de période pour les calculs"
    )
):
    """
    Obtenir les KPI globaux pour une période personnalisée
    
    Args:
        date_debut: Date de début
        date_fin: Date de fin
        periode: Type de période (heure/jour/semaine/mois)
    
    Returns: KPI de la période personnalisée
    """
    try:
        logger.info(f"📊 Requête KPI personnalisée ({periode}) : {date_debut} - {date_fin}")
        
        kpi = await KPIService.calculate_kpi_global(
            periode=periode,
            date_debut=date_debut,
            date_fin=date_fin
        )
        
        kpi_dict = kpi.model_dump(by_alias=True, exclude_none=True, exclude={"id", "created_at"})
        
        response = {
            "success": True,
            "data": kpi_dict
        }
        
        logger.info("✅ KPI personnalisés récupérés avec succès")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur KPI personnalisés : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=dict)
async def get_kpi_history(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours d'historique"),
    periode: Literal["heure", "jour", "semaine", "mois"] = Query(
        "jour",
        description="Type de période des KPI"
    )
):
    """
    Obtenir l'historique des KPI
    
    Args:
        days: Nombre de jours d'historique (1-365)
        periode: Type de période (heure/jour/semaine/mois)
    
    Returns: Liste des KPI historiques
    """
    try:
        logger.info(f"📊 Requête historique KPI ({periode}) : {days} jours")
        
        kpi_list = await KPIService.get_kpi_history(days=days, periode=periode)
        
        # Convertir chaque KPI en dict
        kpi_dicts = [
            kpi.model_dump(by_alias=True, exclude_none=True, exclude={"id", "created_at"})
            for kpi in kpi_list
        ]
        
        response = {
            "success": True,
            "count": len(kpi_dicts),
            "data": kpi_dicts
        }
        
        logger.info(f"✅ Historique KPI récupéré : {len(kpi_dicts)} entrées")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur historique KPI : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=dict)
async def get_latest_kpi(
    periode: Literal["heure", "jour", "semaine", "mois"] = Query(
        "jour",
        description="Type de période"
    )
):
    """
    Obtenir le KPI le plus récent
    
    Args:
        periode: Type de période (heure/jour/semaine/mois)
    
    Returns: KPI le plus récent ou null
    """
    try:
        logger.info(f"📊 Requête dernier KPI : {periode}")
        
        kpi = await KPIService.get_latest_kpi(periode=periode)
        
        if not kpi:
            return {
                "success": True,
                "data": None,
                "message": "Aucun KPI trouvé"
            }
        
        kpi_dict = kpi.model_dump(by_alias=True, exclude_none=True, exclude={"id", "created_at"})
        
        response = {
            "success": True,
            "data": kpi_dict
        }
        
        logger.info("✅ Dernier KPI récupéré avec succès")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur dernier KPI : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/{video_id}/calculate", response_model=dict)
async def calculate_video_kpi(
    video_id: str,
    periode: Literal["heure", "jour", "semaine", "mois"] = Query(
        "heure",
        description="Type de période à calculer à partir de cette vidéo"
    )
):
    """
    Calculer les KPI pour une vidéo spécifique
    
    Args:
        video_id: ID de la vidéo
        periode: Type de période (heure/jour/semaine/mois)
    
    Returns: KPI calculés pour cette vidéo selon la période
    """
    try:
        logger.info(f"📊 Calcul KPI ({periode}) pour vidéo : {video_id}")
        
        kpi = await KPIService.calculate_kpi_for_video(video_id, periode=periode)
        
        kpi_dict = kpi.model_dump(by_alias=True, exclude_none=True, exclude={"id", "created_at"})
        
        response = {
            "success": True,
            "data": kpi_dict,
            "message": f"KPI {periode} calculé et sauvegardé avec succès"
        }
        
        logger.info(f"✅ KPI {periode} calculé pour vidéo {video_id}")
        return response
        
    except ValueError as e:
        logger.error(f"❌ Erreur vidéo : {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur calcul KPI : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/production/trend", response_model=dict)
async def get_production_trend(
    days: int = Query(7, ge=1, le=90, description="Nombre de jours"),
    periode: Literal["heure", "jour", "semaine", "mois"] = Query(
        "jour",
        description="Type de période"
    )
):
    """
    Obtenir la tendance de production
    
    Args:
        days: Nombre de jours pour la tendance
        periode: Type de période (heure/jour/semaine/mois)
    
    Returns: Données de tendance production
    """
    try:
        logger.info(f"📊 Requête tendance production ({periode}) : {days} jours")
        
        kpi_list = await KPIService.get_kpi_history(days=days, periode=periode)
        
        # Extraire seulement les données de production
        production_trend = []
        for kpi in kpi_list:
            if kpi.production:
                production_trend.append({
                    "date": kpi.date.isoformat(),
                    "periode": kpi.periode,
                    "unites_produites": kpi.production.unites_produites,
                    "taux_productivite": kpi.production.taux_productivite,
                    "taux_conformite": kpi.production.taux_conformite
                })
        
        response = {
            "success": True,
            "count": len(production_trend),
            "data": production_trend
        }
        
        logger.info(f"✅ Tendance production récupérée : {len(production_trend)} points")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur tendance production : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/machines/trs-trend", response_model=dict)
async def get_trs_trend(
    days: int = Query(7, ge=1, le=90, description="Nombre de jours"),
    periode: Literal["heure", "jour", "semaine", "mois"] = Query(
        "jour",
        description="Type de période"
    )
):
    """
    Obtenir la tendance TRS des machines
    
    Args:
        days: Nombre de jours pour la tendance
        periode: Type de période (heure/jour/semaine/mois)
    
    Returns: Données de tendance TRS
    """
    try:
        logger.info(f"📊 Requête tendance TRS ({periode}) : {days} jours")
        
        kpi_list = await KPIService.get_kpi_history(days=days, periode=periode)
        
        # Extraire seulement les données TRS
        trs_trend = []
        for kpi in kpi_list:
            if kpi.machines:
                trs_trend.append({
                    "date": kpi.date.isoformat(),
                    "periode": kpi.periode,
                    "trs": kpi.machines.trs,
                    "disponibilite": kpi.machines.disponibilite,
                    "performance": kpi.machines.performance,
                    "qualite": kpi.machines.qualite
                })
        
        response = {
            "success": True,
            "count": len(trs_trend),
            "data": trs_trend
        }
        
        logger.info(f"✅ Tendance TRS récupérée : {len(trs_trend)} points")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur tendance TRS : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))