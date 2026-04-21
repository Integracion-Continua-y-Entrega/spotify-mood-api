import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

load_dotenv()

# Configuración de logs para monitorear la conexión
logger = logging.getLogger("uvicorn.error")

class MongoDB:
    """Clase Singleton para gestionar la conexión a MongoDB."""
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls.client is None:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                logger.error("❌ MONGO_URI no definida en .env")
                raise RuntimeError("MONGO_URI no configurada.")
            
            # Configuramos el cliente con un pool de conexiones optimizado
            cls.client = AsyncIOMotorClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=1
            )
            logger.info("🔌 Cliente MongoDB inicializado.")
        return cls.client

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        if cls.database is None:
            db_name = os.getenv("MONGO_DB", "music_recommendations")
            client = cls.get_client()
            cls.database = client[db_name]
        return cls.database

    @classmethod
    async def close_connection(cls):
        if cls.client:
            cls.client.close()
            logger.info("🛑 Conexión a MongoDB cerrada.")

# Función de conveniencia para main.py
def get_database() -> AsyncIOMotorDatabase:
    return MongoDB.get_db()