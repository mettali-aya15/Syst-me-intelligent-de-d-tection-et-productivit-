from fastapi import WebSocket, APIRouter
from app.services.realtime.websocket import ConnectionManager
from .routes.cameras import router as cameras_router
from .routes.workstation import router as workstations_router
from .routes.employees import router as employees_router
from .routes.events import router as events_router
from .routes.kpis import router as kpis_router
from .routes.reports import router as reports_router
from .routes.alerts import router as alerts_router
from .routes.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(cameras_router, prefix="/cameras", tags=["Cameras"])
api_router.include_router(workstations_router, prefix="/workstations", tags=["Workstations"])
api_router.include_router(employees_router, prefix="/employees", tags=["Employees"])
api_router.include_router(events_router, prefix="/events", tags=["Events"])
api_router.include_router(kpis_router, prefix="/kpis", tags=["KPIs"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

manager = ConnectionManager()

@api_router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Ici on pourrait recevoir des commandes depuis le client si besoin
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)