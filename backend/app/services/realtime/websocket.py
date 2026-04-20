#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire WebSocket pour notifications temps réel
"""

from typing import List, Dict, Set
from fastapi import WebSocket
from datetime import datetime
import json
import asyncio

import logging
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gestionnaire de connexions WebSocket"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        self.subscriptions: Dict[str, Set[WebSocket]] = {}  # topic -> {websockets}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """
        Accepter une nouvelle connexion WebSocket
        
        Args:
            websocket: Connexion WebSocket
            client_id: ID du client (optionnel)
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        
        metadata = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": datetime.now(),
            "subscriptions": set()
        }
        
        self.connection_metadata[websocket] = metadata
        
        logger.info(f"✅ WebSocket connecté : {metadata['client_id']} (Total: {len(self.active_connections)})")
        
        # Envoyer message de bienvenue
        await self.send_personal_message({
            "type": "connection_established",
            "client_id": metadata["client_id"],
            "server_time": datetime.now().isoformat(),
            "message": "Connexion WebSocket établie avec succès"
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """
        Déconnecter un client
        
        Args:
            websocket: Connexion à fermer
        """
        if websocket in self.active_connections:
            metadata = self.connection_metadata.get(websocket, {})
            client_id = metadata.get("client_id", "unknown")
            
            # Retirer des souscriptions
            subscriptions = metadata.get("subscriptions", set())
            for topic in subscriptions:
                if topic in self.subscriptions:
                    self.subscriptions[topic].discard(websocket)
            
            # Retirer de la liste
            self.active_connections.remove(websocket)
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            logger.info(f"❌ WebSocket déconnecté : {client_id} (Restants: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """
        Envoyer un message à un client spécifique
        
        Args:
            message: Message à envoyer
            websocket: Connexion cible
        """
        try:
            if not message.get("timestamp"):
                message["timestamp"] = datetime.now().isoformat()
            
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"❌ Erreur envoi message personnel : {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict, exclude: WebSocket = None):
        """
        Diffuser un message à tous les clients connectés
        
        Args:
            message: Message à diffuser
            exclude: Connexion à exclure (optionnel)
        """
        if not message.get("timestamp"):
            message["timestamp"] = datetime.now().isoformat()
        
        disconnected = []
        
        for connection in self.active_connections:
            if connection == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"❌ Erreur broadcast : {e}")
                disconnected.append(connection)
        
        # Nettoyer les connexions mortes
        for conn in disconnected:
            self.disconnect(conn)
        
        if len(self.active_connections) > 0:
            logger.debug(f"📡 Message diffusé à {len(self.active_connections) - len(disconnected)} clients")
    
    async def subscribe(self, websocket: WebSocket, topic: str):
        """
        Souscrire un client à un topic
        
        Args:
            websocket: Connexion du client
            topic: Topic à souscrire (ex: "video_processing", "alerts", "kpis")
        """
        if websocket not in self.active_connections:
            return
        
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(websocket)
        self.connection_metadata[websocket]["subscriptions"].add(topic)
        
        logger.info(f"📌 Client souscrit au topic : {topic}")
        
        await self.send_personal_message({
            "type": "subscription_confirmed",
            "topic": topic,
            "message": f"Souscription au topic '{topic}' confirmée"
        }, websocket)
    
    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """
        Désouscrire un client d'un topic
        
        Args:
            websocket: Connexion du client
            topic: Topic à quitter
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(websocket)
        
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].discard(topic)
        
        logger.info(f"📌 Client désouscrit du topic : {topic}")
    
    async def publish_to_topic(self, topic: str, message: Dict):
        """
        Publier un message sur un topic spécifique
        
        Args:
            topic: Topic cible
            message: Message à publier
        """
        if topic not in self.subscriptions:
            return
        
        if not message.get("timestamp"):
            message["timestamp"] = datetime.now().isoformat()
        
        message["topic"] = topic
        
        disconnected = []
        subscribers = list(self.subscriptions[topic])
        
        for websocket in subscribers:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"❌ Erreur publication topic : {e}")
                disconnected.append(websocket)
        
        # Nettoyer
        for conn in disconnected:
            self.disconnect(conn)
        
        logger.debug(f"📡 Message publié sur topic '{topic}' à {len(subscribers) - len(disconnected)} clients")
    
    # ========== MÉTHODES SPÉCIFIQUES CAMIA-FACTORY ==========
    
    async def send_video_processing_started(self, video_id: str, filename: str):
        """Notifier démarrage traitement vidéo"""
        await self.publish_to_topic("video_processing", {
            "type": "processing_started",
            "video_id": video_id,
            "filename": filename
        })
    
    async def send_video_processing_progress(
        self, 
        video_id: str, 
        current_frame: int, 
        total_frames: int
    ):
        """
        Envoyer la progression de traitement vidéo
        
        Args:
            video_id: ID de la vidéo
            current_frame: Frame actuelle
            total_frames: Total de frames
        """
        progress = int((current_frame / total_frames) * 100) if total_frames > 0 else 0
        
        await self.publish_to_topic("video_processing", {
            "type": "processing_progress",
            "video_id": video_id,
            "current_frame": current_frame,
            "total_frames": total_frames,
            "progress": progress
        })
    
    async def send_video_processing_completed(
        self, 
        video_id: str, 
        total_detections: int,
        summary: Dict
    ):
        """Notifier fin de traitement vidéo"""
        await self.publish_to_topic("video_processing", {
            "type": "processing_completed",
            "video_id": video_id,
            "total_detections": total_detections,
            "summary": summary
        })
    
    async def send_video_processing_failed(self, video_id: str, error: str):
        """Notifier échec de traitement"""
        await self.publish_to_topic("video_processing", {
            "type": "processing_failed",
            "video_id": video_id,
            "error": error
        })
    
    async def send_alert(
        self, 
        alert_id: str,
        alert_type: str, 
        severity: str, 
        message: str,
        metadata: Dict = None
    ):
        """
        Envoyer une alerte à tous les clients
        
        Args:
            alert_id: ID de l'alerte
            alert_type: Type d'alerte
            severity: Sévérité (low, medium, high, critical)
            message: Message
            metadata: Données additionnelles
        """
        await self.publish_to_topic("alerts", {
            "type": "new_alert",
            "alert_id": alert_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "metadata": metadata or {}
        })
        
        # Broadcast aussi pour importance critique
        if severity in ["high", "critical"]:
            await self.broadcast({
                "type": "critical_alert",
                "alert_id": alert_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message
            })
    
    async def send_alert_resolved(self, alert_id: str, resolved_by: str):
        """Notifier résolution d'alerte"""
        await self.publish_to_topic("alerts", {
            "type": "alert_resolved",
            "alert_id": alert_id,
            "resolved_by": resolved_by
        })
    
    async def send_kpi_update(self, kpis: Dict):
        """
        Envoyer une mise à jour des KPIs
        
        Args:
            kpis: KPIs à envoyer
        """
        await self.publish_to_topic("kpis", {
            "type": "kpi_update",
            "kpis": kpis
        })
    
    async def send_employee_detected(self, employee_name: str, video_id: str):
        """Notifier détection d'employé"""
        await self.publish_to_topic("detections", {
            "type": "employee_detected",
            "employee_name": employee_name,
            "video_id": video_id
        })
    
    async def send_machine_status_changed(
        self, 
        machine_id: str,
        machine_name: str, 
        old_status: str, 
        new_status: str
    ):
        """Notifier changement statut machine"""
        await self.publish_to_topic("machines", {
            "type": "machine_status_changed",
            "machine_id": machine_id,
            "machine_name": machine_name,
            "old_status": old_status,
            "new_status": new_status
        })
    
    async def send_event(self, event_type: str, data: Dict):
        """
        Envoyer un événement générique
        
        Args:
            event_type: Type d'événement
            data: Données de l'événement
        """
        await self.broadcast({
            "type": event_type,
            "data": data
        })
    
    async def send_heartbeat(self):
        """
        Envoyer un heartbeat à tous les clients
        (Pour maintenir la connexion active)
        """
        await self.broadcast({
            "type": "heartbeat",
            "server_time": datetime.now().isoformat(),
            "active_connections": len(self.active_connections)
        })
    
    # ========== MÉTHODES UTILITAIRES ==========
    
    def get_active_connections_count(self) -> int:
        """Obtenir le nombre de connexions actives"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict]:
        """Obtenir les infos des connexions actives"""
        return [
            {
                "client_id": meta["client_id"],
                "connected_at": meta["connected_at"].isoformat(),
                "subscriptions": list(meta.get("subscriptions", set()))
            }
            for meta in self.connection_metadata.values()
        ]
    
    def get_topic_subscribers_count(self, topic: str) -> int:
        """Obtenir le nombre de souscripteurs d'un topic"""
        return len(self.subscriptions.get(topic, set()))
    
    async def handle_client_message(self, websocket: WebSocket, message: Dict):
        """
        Gérer un message reçu d'un client
        
        Args:
            websocket: Connexion du client
            message: Message reçu
        """
        msg_type = message.get("type")
        
        if msg_type == "subscribe":
            topic = message.get("topic")
            if topic:
                await self.subscribe(websocket, topic)
        
        elif msg_type == "unsubscribe":
            topic = message.get("topic")
            if topic:
                await self.unsubscribe(websocket, topic)
        
        elif msg_type == "ping":
            await self.send_personal_message({
                "type": "pong",
                "message": "Connexion active"
            }, websocket)
        
        elif msg_type == "get_status":
            await self.send_personal_message({
                "type": "status",
                "active_connections": self.get_active_connections_count(),
                "your_subscriptions": list(self.connection_metadata[websocket]["subscriptions"])
            }, websocket)
        
        else:
            logger.warning(f"⚠️ Type de message inconnu : {msg_type}")


# Instance globale du gestionnaire
manager = ConnectionManager()


async def start_heartbeat_task():
    """Tâche en arrière-plan pour envoyer des heartbeats"""
    while True:
        await asyncio.sleep(30)  # Toutes les 30 secondes
        await manager.send_heartbeat()