from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    
    @classmethod
    async def connect(cls):
        try:
            from app.core.config import settings
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            cls.db = cls.client[settings.MONGODB_DB]
            await cls.client.admin.command('ping')
            logger.info(f"✅ MongoDB connecté : {settings.MONGODB_DB}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion MongoDB : {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            logger.info("✅ MongoDB déconnecté")
    
    @classmethod
    def get_collection(cls, collection_name: str):
        if cls.db is None:
            raise Exception("Database not connected")
        return cls.db[collection_name]