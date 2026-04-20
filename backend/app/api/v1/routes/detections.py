#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les détections
Consultation et statistiques des détections
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from bson import ObjectId

from core.database import Database

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/video/{video_id}")
async def get_video_detections(
    video_id: str,
    limit: int = Query(1000, ge=1, le=10000),
    skip: int = Query(0, ge=0)
):
    """
    Obtenir les détections d'une vidéo
    
    - **video_id**: ID de la vidéo
    - **limit**: Nombre maximum de détections
    - **skip**: Nombre de détections à sauter
    
    Returns:
        Liste des détections
    """
    try:
        collection = Database.get_collection("video_detections")
        
        cursor = collection.find(
            {"video_id": ObjectId(video_id)}
        ).sort("frame_number", 1).skip(skip).limit(limit)
        
        detections = await cursor.to_list(length=limit)
        
        return {
            "video_id": video_id,
            "count": len(detections),
            "detections": [
                {
                    "frame_number": det["frame_number"],
                    "timestamp": det["timestamp"],
                    "class_name": det["class_name"],
                    "confidence": det["confidence"],
                    "bbox": det["bbox"],
                    "source": det["source"]
                }
                for det in detections
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur récupération détections : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/{video_id}/summary")
async def get_detections_summary(video_id: str):
    """
    Obtenir un résumé des détections d'une vidéo
    
    - **video_id**: ID de la vidéo
    
    Returns:
        Résumé par classe
    """
    try:
        collection = Database.get_collection("video_detections")
        
        # Agréger par classe
        pipeline = [
            {"$match": {"video_id": ObjectId(video_id)}},
            {
                "$group": {
                    "_id": "$class_name",
                    "count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence"}
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        summary = {
            result["_id"]: {
                "count": result["count"],
                "avg_confidence": round(result["avg_confidence"], 3)
            }
            for result in results
        }
        
        total_detections = sum(r["count"] for r in summary.values())
        
        return {
            "video_id": video_id,
            "total_detections": total_detections,
            "by_class": summary
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur résumé détections : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/{video_id}/timeline")
async def get_detections_timeline(
    video_id: str,
    class_name: Optional[str] = None
):
    """
    Obtenir la timeline des détections
    
    - **video_id**: ID de la vidéo
    - **class_name**: Filtrer par classe (optionnel)
    
    Returns:
        Timeline des détections
    """
    try:
        collection = Database.get_collection("video_detections")
        
        query = {"video_id": ObjectId(video_id)}
        if class_name:
            query["class_name"] = class_name
        
        cursor = collection.find(query).sort("timestamp", 1)
        detections = await cursor.to_list(length=None)
        
        # Regrouper par seconde
        timeline = {}
        for det in detections:
            second = int(det["timestamp"])
            if second not in timeline:
                timeline[second] = []
            
            timeline[second].append({
                "class_name": det["class_name"],
                "confidence": det["confidence"]
            })
        
        return {
            "video_id": video_id,
            "class_filter": class_name,
            "timeline": [
                {
                    "second": second,
                    "detections": dets
                }
                for second, dets in sorted(timeline.items())
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur timeline détections : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/global")
async def get_global_detection_stats():
    """
    Obtenir les statistiques globales de détection
    
    Returns:
        Statistiques globales
    """
    try:
        collection = Database.get_collection("video_detections")
        
        # Total de détections
        total = await collection.count_documents({})
        
        # Par classe
        pipeline = [
            {
                "$group": {
                    "_id": "$class_name",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        
        cursor = collection.aggregate(pipeline)
        by_class = await cursor.to_list(length=20)
        
        # Par source
        pipeline_source = [
            {
                "$group": {
                    "_id": "$source",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        cursor_source = collection.aggregate(pipeline_source)
        by_source = await cursor_source.to_list(length=None)
        
        return {
            "total_detections": total,
            "by_class": {
                item["_id"]: item["count"]
                for item in by_class
            },
            "by_source": {
                item["_id"]: item["count"]
                for item in by_source
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur stats globales : {e}")
        raise HTTPException(status_code=500, detail=str(e))