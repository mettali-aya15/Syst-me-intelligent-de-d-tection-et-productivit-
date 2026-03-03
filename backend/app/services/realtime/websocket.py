import json
from fastapi import WebSocket
from app.models.workstation import Workstation
#from app.services.workstation_service import get_workstation_by_id
#from app.services.kpi_calculator import KPICalculator

class ConnectionManager:
    """
    Gestionnaire de WebSockets
    """
    
    def __init__(self):
        self.active_connections = {}
    
    async def connect(self, websocket: WebSocket, workstation_id: int):
        """Établit une connexion WebSocket"""
        await websocket.accept()
        self.active_connections[workstation_id] = websocket
    
    def disconnect(self, workstation_id: int):
        """Déconnecte une WebSocket"""
        if workstation_id in self.active_connections:
            del self.active_connections[workstation_id]
    
    async def send_kpi_update(self, workstation_id: int):
        """Envoie une mise à jour KPI à un client WebSocket"""
        if workstation_id in self.active_connections:
            kpi = KPICalculator.get_workstation_kpi(workstation_id)
            await self.active_connections[workstation_id].send_json({
                "type": "kpi_update",
                "data": kpi
            })
    
    async def send_event_update(self, workstation_id: int, event: dict):
        """Envoie une mise à jour d'événement à un client WebSocket"""
        if workstation_id in self.active_connections:
            await self.active_connections[workstation_id].send_json({
                "type": "event_update",
                "data": event
            })
    
    async def broadcast_kpi_update(self, site_id: int):
        """Envoie une mise à jour KPI à tous les clients connectés à un site"""
        # Logique pour envoyer aux clients connectés au site
        pass
    
    async def broadcast_event_update(self, site_id: int, event: dict):
        """Envoie une mise à jour d'événement à tous les clients connectés à un site"""
        # Logique pour envoyer aux clients connectés au site
        pass