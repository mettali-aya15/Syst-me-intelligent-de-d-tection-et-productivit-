from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    """Gestionnaire de connexions WebSocket"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepter une nouvelle connexion WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ Client WebSocket connecté. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Retirer une connexion WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 Client WebSocket déconnecté. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Envoyer un message à tous les clients connectés
        
        Args:
            message: Dictionnaire contenant le message à envoyer
        """
        if not self.active_connections:
            logger.warning("⚠️ Aucun client WebSocket connecté pour recevoir le message")
            return
        
        logger.info(f"📤 Broadcast vers {len(self.active_connections)} client(s): {message.get('type')}")
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.info(f"✅ Message envoyé à un client")
            except Exception as e:
                logger.error(f"❌ Erreur envoi message WebSocket: {e}")
                disconnected.append(connection)
        
        # Nettoyer les connexions mortes
        for conn in disconnected:
            self.disconnect(conn)

# Instance globale du gestionnaire
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket pour les notifications en temps réel
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Recevoir des messages du client (ping/pong, heartbeat, etc.)
            data = await websocket.receive_text()
            logger.info(f"📨 Message reçu du client: {data}")
            
            # Echo pour test de connexion
            await websocket.send_json({
                "type": "echo",
                "data": data
            })
            
    except WebSocketDisconnect:
        logger.info("🔌 Client déconnecté (WebSocketDisconnect)")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket: {e}")
        manager.disconnect(websocket)