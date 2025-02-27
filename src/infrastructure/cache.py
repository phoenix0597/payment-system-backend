from typing import Optional
import redis.asyncio as redis
from src.config.config import settings


class RedisCacheAdapter:
    """Адаптер для работы с Redis как инфраструктурным кэшем."""

    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
        )

    async def get(self, key: str) -> Optional[str]:
        """Получить необработанные данные из Redis."""
        return await self.client.get(key)

    async def set(self, key: str, value: str, expire: int = 300) -> None:
        """Записать данные в Redis с TTL."""
        await self.client.setex(key, expire, value)

    async def delete(self, key: str) -> None:
        """Удалить данные из Redis."""
        await self.client.delete(key)

    async def close(self) -> None:
        """Закрыть соединение с Redis."""
        await self.client.close()


def get_redis_cache_adapter() -> RedisCacheAdapter:
    """Получить экземпляр адаптера Redis."""
    return RedisCacheAdapter()
