#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les rapports
Export PDF, CSV, JSON
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional
from datetime import date
from pathlib import Path


import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/daily/export")
async def export_daily_report(
    target_date: date,
    format: str = Query("json", regex="^(json|csv|txt)$")
):
    """
    Exporter un rapport journalier
    
    - **target_date**: Date du rapport (format: YYYY-MM-DD)
    - **format**: Format d'export (json, csv, txt)
    
    Returns:
        Fichier téléchargeable
    """
    try:
        filepath = await ReportGenerator.export_daily_report(
            target_date=target_date,
            format=format
        )
        
        if not Path(filepath).exists():
            raise HTTPException(status_code=404, detail="Fichier non généré")
        
        media_type_map = {
            "json": "application/json",
            "csv": "text/csv",
            "txt": "text/plain"
        }
        
        return FileResponse(
            path=filepath,
            media_type=media_type_map.get(format, "application/octet-stream"),
            filename=Path(filepath).name
        )
    
    except Exception as e:
        logger.error(f"❌ Erreur export rapport : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/productivity/chart-data")
async def get_productivity_chart_data(
    start_date: date,
    end_date: date
):
    """
    Obtenir les données pour graphique de productivité
    
    - **start_date**: Date de début
    - **end_date**: Date de fin
    
    Returns:
        Données formatées pour Chart.js
    """
    try:
        chart_data = await ReportGenerator.generate_productivity_chart_data(
            start_date=start_date,
            end_date=end_date
        )
        
        return chart_data
    
    except Exception as e:
        logger.error(f"❌ Erreur données graphique : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/custom")
async def generate_custom_report(
    report_data: dict,
    format: str = Query("json", regex="^(json|csv|txt)$")
):
    """
    Générer un rapport personnalisé
    
    - **report_data**: Données du rapport
    - **format**: Format de sortie
    
    Returns:
        Fichier téléchargeable
    """
    try:
        if format == "json":
            filepath = await ReportGenerator.generate_json_report(report_data)
        elif format == "txt":
            filepath = await ReportGenerator.generate_text_summary(report_data)
        else:
            raise HTTPException(
                status_code=400,
                detail="Format CSV nécessite une structure spécifique"
            )
        
        return FileResponse(
            path=filepath,
            filename=Path(filepath).name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport personnalisé : {e}")
        raise HTTPException(status_code=500, detail=str(e))