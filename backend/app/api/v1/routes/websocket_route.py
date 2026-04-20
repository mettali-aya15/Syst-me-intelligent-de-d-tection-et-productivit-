#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Route WebSocket pour notifications temps réel
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json

from app.services.realtime.websocket import manager

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    Endpoint WebSocket pour connexion temps réel
    
    - **client_id**: ID optionnel du client
    
    Usage côté client (JavaScript):
    ```javascript
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
        console.log(event.data);
    };

    ws.onclose = () => {
        console.log("Connexion fermée");
    };
    ```
    """

    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Exemple : broadcast du message à tous les clients
            await manager.broadcast(message)

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"Client déconnecté: {client_id}")