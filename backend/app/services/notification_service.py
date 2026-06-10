#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de gestion des notifications
Création et envoi de notifications via WebSocket + sauvegarde MongoDB
"""

from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId

from app.core.database import Database
from app.services.realtime.websocket import manager

import logging
logger = logging.getLogger(__name__)


class NotificationService:
    """Service pour créer et gérer les notifications"""
    
    @staticmethod
    async def create_notification(
        notification_type: str,
        severity: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Créer une notification, la sauvegarder dans MongoDB et l'envoyer via WebSocket
        
        Args:
            notification_type: Type de notification (video_complete, kpi_update, alert, etc.)
            severity: Sévérité (low, medium, high, critical)
            title: Titre de la notification
            message: Message détaillé
            data: Données additionnelles (optionnel)
            
        Returns:
            ID de la notification créée
        """
        try:
            notification = {
                "type": notification_type,
                "severity": severity,
                "title": title,
                "message": message,
                "data": data or {},
                "created_at": datetime.now()
            }
            
            # Sauvegarder dans MongoDB
            collection = Database.get_collection("notifications")
            result = await collection.insert_one(notification)
            
            logger.info(f"📬 Notification créée dans MongoDB : {title} (ID: {result.inserted_id})")
            
            # Envoyer via WebSocket
            await manager.broadcast({
                "type": "notification",
                "notification": {
                    "id": str(result.inserted_id),
                    "type": notification_type,
                    "severity": severity,
                    "title": title,
                    "message": message,
                    "data": data or {},
                    "created_at": notification["created_at"].isoformat()
                }
            })
            
            logger.info(f"📡 Notification envoyée via WebSocket : {title}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Erreur création notification : {e}")
            raise
    
    @staticmethod
    async def notify_video_complete(
        video_id: str,
        filename: str,
        total_detections: int,
        unique_objects: Dict = None
    ):
        """
        Notification automatique : analyse vidéo terminée
        
        Args:
            video_id: ID de la vidéo
            filename: Nom du fichier vidéo
            total_detections: Nombre total de détections
            unique_objects: Objets uniques détectés
        """
        await NotificationService.create_notification(
            notification_type="video_complete",
            severity="low",
            title="Analyse vidéo terminée",
            message=f"La vidéo '{filename}' a été analysée avec succès : {total_detections} détections",
            data={
                "video_id": video_id,
                "filename": filename,
                "total_detections": total_detections,
                "unique_objects": unique_objects or {}
            }
        )
    
    @staticmethod
    async def notify_video_failed(
        video_id: str,
        filename: str,
        error: str
    ):
        """
        Notification automatique : échec d'analyse vidéo
        """
        await NotificationService.create_notification(
            notification_type="video_failed",
            severity="high",
            title="Erreur d'analyse vidéo",
            message=f"L'analyse de '{filename}' a échoué : {error}",
            data={
                "video_id": video_id,
                "filename": filename,
                "error": error
            }
        )
    
    @staticmethod
    async def notify_kpi_updated(
        kpi_data: Dict
    ):
        """
        Notification automatique : KPIs mis à jour
        """
        await NotificationService.create_notification(
            notification_type="kpi_update",
            severity="low",
            title="KPIs mis à jour",
            message="Les indicateurs de performance ont été calculés avec succès",
            data=kpi_data
        )
    
    @staticmethod
    async def notify_alert(
        alert_type: str,
        severity: str,
        message: str,
        metadata: Dict = None
    ):
        """
        Notification automatique : alerte système
        """
        await NotificationService.create_notification(
            notification_type="alert",
            severity=severity,
            title=f"Alerte : {alert_type}",
            message=message,
            data=metadata or {}
        )
    
    @staticmethod
    async def get_user_notifications(
        limit: int = 50,
        skip: int = 0,
        unread_only: bool = False
    ) -> list:
        """
        Récupérer les notifications d'un utilisateur
        
        Args:
            limit: Nombre max de notifications à retourner
            skip: Nombre de notifications à sauter
            unread_only: Ne retourner que les non lues
            
        Returns:
            Liste des notifications
        """
        try:
            collection = Database.get_collection("notifications")
            
            if unread_only:
                query["read"] = False
            
            cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            notifications = await cursor.to_list(length=limit)
            
            return notifications
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération notifications : {e}")
            return []
