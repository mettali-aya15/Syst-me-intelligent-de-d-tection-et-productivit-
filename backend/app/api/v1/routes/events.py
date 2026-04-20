#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les événements
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from core.database import Database

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """
    Lister les événements
    
    - **event_type**: Filtrer par type
    - **severity**: Filtrer par sévérité
    
    Returns:
        Liste des événements
    """
    try:
        collection = Database.get_collection("events")
        
        query = {}
        if event_type:
            query["type"] = event_type
        if severity:
            query["severity"] = severity
        
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        events = await cursor.to_list(length=limit)
        
        return {
            "count": len(events),
            "events": [
                {
                    "id": str(evt["_id"]),
                    "type": evt["type"],
                    "message": evt["message"],
                    "severity": evt["severity"],
                    "created_at": evt["created_at"],
                    "is_resolved": evt.get("is_resolved", False)
                }
                for evt in events
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur listage événements : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_events(hours: int = Query(24, ge=1, le=168)):
    """
    Obtenir les événements récents
    
    - **hours**: Nombre d'heures en arrière
    
    Returns:
        Événements récents
    """
    try:
        collection = Database.get_collection("events")
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor = collection.find({
            "created_at": {"$gte": cutoff_time}
        }).sort("created_at", -1)
        
        events = await cursor.to_list(length=None)
        
        return {
            "period_hours": hours,
            "count": len(events),
            "events": [
                {
                    "id": str(evt["_id"]),
                    "type": evt["type"],
                    "message": evt["message"],
                    "severity": evt["severity"],
                    "created_at": evt["created_at"]
                }
                for evt in events
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur événements récents : {e}")
        raise HTTPException(status_code=500, detail=str(e))