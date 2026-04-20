#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les alertes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId

from core.database import Database

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_alerts(
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """
    Lister les alertes
    
    - **is_resolved**: Filtrer par statut résolu
    - **severity**: Filtrer par sévérité
    
    Returns:
        Liste des alertes
    """
    try:
        collection = Database.get_collection("alerts")
        
        query = {}
        if is_resolved is not None:
            query["is_resolved"] = is_resolved
        if severity:
            query["severity"] = severity
        
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        alerts = await cursor.to_list(length=limit)
        
        return {
            "count": len(alerts),
            "alerts": [
                {
                    "id": str(alert["_id"]),
                    "type": alert["alert_type"],
                    "severity": alert["severity"],
                    "message": alert["message"],
                    "is_resolved": alert["is_resolved"],
                    "created_at": alert["created_at"],
                    "resolved_at": alert.get("resolved_at")
                }
                for alert in alerts
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur listage alertes : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolved_by: Optional[str] = None,
    resolution_note: Optional[str] = None
):
    """
    Résoudre une alerte
    
    - **alert_id**: ID de l'alerte
    - **resolved_by**: Qui a résolu (optionnel)
    - **resolution_note**: Note de résolution (optionnel)
    
    Returns:
        Alerte résolue
    """
    try:
        collection = Database.get_collection("alerts")
        
        update_data = {
            "is_resolved": True,
            "resolved_at": datetime.now()
        }
        
        if resolved_by:
            update_data["resolved_by"] = resolved_by
        if resolution_note:
            update_data["resolution_note"] = resolution_note
        
        result = await collection.find_one_and_update(
            {"_id": ObjectId(alert_id)},
            {"$set": update_data},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Alerte introuvable")
        
        return {
            "message": "Alerte résolue avec succès",
            "alert_id": alert_id,
            "resolved_at": update_data["resolved_at"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur résolution alerte : {e}")
        raise HTTPException(status_code=500, detail=str(e))