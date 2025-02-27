from datetime import datetime
from decimal import Decimal
from typing import Optional, TypeVar, Generic
from src.infrastructure.cache import RedisCacheAdapter, get_redis_cache_adapter
import json
from src.core.logger import log

T = TypeVar("T")


class CustomJSONEncoder(json.JSONEncoder):
    """Кастомный энкодер для сериализации Decimal в JSON."""

    def default(self, obj):
        # Преобразуем несериализуемый тип Decimal в строку
        if isinstance(obj, Decimal):
            return str(obj)
        # Преобразуем datetime в строку ISO 8601
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class CacheService(Generic[T]):
    """Сервис кэширования для бизнес-логики."""

    def __init__(self, cache_adapter: RedisCacheAdapter):
        self.cache_adapter = cache_adapter

    async def get(self, key: str) -> Optional[T]:
        """Получить данные из кэша с десериализацией."""
        data = await self.cache_adapter.get(key)
        if data:
            log.debug(f"Cache hit for key: {key}")
            return json.loads(data)
        log.debug(f"Cache miss for key: {key}")
        return None

    async def set(self, key: str, value: T, expire: int = 300) -> None:
        """Записать данные в кэш с сериализацией."""
        serialized_value = json.dumps(value, cls=CustomJSONEncoder)
        await self.cache_adapter.set(key, serialized_value, expire)
        log.debug(f"Cache set for key: {key} with TTL: {expire}")

    async def delete(self, key: str) -> None:
        """Удалить данные из кэша."""
        await self.cache_adapter.delete(key)
        log.debug(f"Cache deleted for key: {key}")


def get_cache_service(
    adapter: RedisCacheAdapter = get_redis_cache_adapter(),
) -> CacheService:
    """Получить экземпляр сервиса кэширования."""
    return CacheService(adapter)
