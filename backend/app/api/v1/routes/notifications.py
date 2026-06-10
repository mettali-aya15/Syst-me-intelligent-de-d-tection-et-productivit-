#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les notifications
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.services.notification_service import NotificationService

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Lister les notifications d'un utilisateur
    """
    try:
        notifications = await NotificationService.get_user_notifications(
            limit=limit,
            skip=skip,
            unread_only=unread_only
        )
        
        return {
            "count": len(notifications),
            "notifications": [
                {
                    "id": str(notif["_id"]),
                    "type": notif["type"],
                    "severity": notif["severity"],
                    "title": notif["title"],
                    "message": notif["message"],
                    "data": notif.get("data", {}),
                    "created_at": notif["created_at"]
                }
                for notif in notifications
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur listage notifications : {e}")
        raise HTTPException(status_code=500, detail=str(e))
