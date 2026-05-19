#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Point d'entrée principal de l'application FastAPI
CAMIA-Factory Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))

from app.api.v1.routes.router import api_router
from app.api.v1.routes import websocket_route  # ✅ CORRIGÉ
from app.core.database import Database
from app.core.config import settings

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    
    logger.info("=" * 80)
    logger.info("DEMARRAGE CAMIA-FACTORY BACKEND")
    logger.info("=" * 80)
    
    try:
        logger.info("🔌 Tentative de connexion MongoDB...")
        await Database.connect()
        
        logger.info(f"✅ Database.client = {Database.client}")
        logger.info(f"✅ Database.db = {Database.db}")
        logger.info(f"✅ Database.db is None? {Database.db is None}")
        
        try:
            test_collection = Database.get_collection("video_uploads")
            logger.info(f"✅ Test get_collection réussi : {test_collection.name}")
        except Exception as e:
            logger.error(f"❌ Échec get_collection : {e}")
        
        logger.info("✅ Base de données connectée")
        
        required_dirs = [
            settings.UPLOAD_DIR,
            settings.ANNOTATED_DIR,
            "logs",
            "data/reports"
        ]
        
        for dir_path in required_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Dossier vérifié : {dir_path}")
        
        logger.info("=" * 80)
        logger.info("✅ Serveur démarré sur http://0.0.0.0:8000")
        logger.info("📚 Documentation API : http://localhost:8000/docs")
        logger.info("🔌 WebSocket : ws://localhost:8000/api/v1/ws")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage : {e}")
        import traceback
        traceback.print_exc()
        raise
    
    yield
    
    logger.info("=" * 80)
    logger.info("ARRET CAMIA-FACTORY BACKEND")
    logger.info("=" * 80)
    
    try:
        await Database.disconnect()
        logger.info("✅ Base de données déconnectée")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'arrêt : {e}")
    
    logger.info("👋 Au revoir")
    logger.info("=" * 80)


app = FastAPI(
    title="CAMIA-Factory API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:3000",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_path = Path(__file__).parent / "data"
if data_path.exists():
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")
    logger.info(f"✅ Dossier 'data' monté en statique : {data_path}")
else:
    logger.warning(f"⚠️ Dossier 'data' introuvable : {data_path}")

app.include_router(api_router, prefix="/api/v1")

# ✅ Route WebSocket
app.include_router(
    websocket_route.router,  # ✅ CORRIGÉ
    prefix="/api/v1",
    tags=["WebSocket"]
)


@app.get("/")
async def root():
    return {
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    db_status = "connected" if Database.client else "disconnected"

    critical_dirs_ok = all(
        Path(dir_path).exists()
        for dir_path in [settings.UPLOAD_DIR, settings.ANNOTATED_DIR]
    )

    return {
        "status": "healthy" if db_status == "connected" and critical_dirs_ok else "degraded",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )