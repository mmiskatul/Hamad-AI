from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_motor_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    return get_motor_client()[settings.mongo_db_name]


async def close_motor_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
