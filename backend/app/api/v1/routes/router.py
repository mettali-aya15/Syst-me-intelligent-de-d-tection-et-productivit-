#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router principal API v1
Regroupe toutes les routes
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .videos import router as videos_router
from .detections import router as detections_router
from .employees import router as employees_router
from .machines import router as machines_router
from .events import router as events_router
from .kpis import router as kpis_router
from .dashboard import router as dashboard_router
from .alerts import router as alerts_router
from .reports import router as reports_router
from .websocket_route import router as websocket_router


api_router = APIRouter()

# Authentification
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentification"]
)

# Vidéos
api_router.include_router(
    videos_router,
    prefix="/videos",
    tags=["Vidéos"]
)

# Détections
api_router.include_router(
    detections_router,
    prefix="/detections",
    tags=["Détections"]
)

# Employés
api_router.include_router(
    employees_router,
    prefix="/employees",
    tags=["Employés"]
)

# Machines
api_router.include_router(
    machines_router,
    prefix="/machines",
    tags=["Machines"]
)

# Événements
api_router.include_router(
    events_router,
    prefix="/events",
    tags=["Événements"]
)

# KPIs
api_router.include_router(
    kpis_router,
    prefix="/kpis",
    tags=["KPIs"]
)

# Dashboard
api_router.include_router(
    dashboard_router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

# Alertes
api_router.include_router(
    alerts_router,
    prefix="/alerts",
    tags=["Alertes"]
)

# Rapports
api_router.include_router(
    reports_router,
    prefix="/reports",
    tags=["Rapports"]
)

# WebSocket
api_router.include_router(
    websocket_router,
    tags=["WebSocket"]
)