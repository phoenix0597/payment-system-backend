# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.main import app
from src.infrastructure.database import Base, get_session
from src.config.config import Settings
from fakeredis.aioredis import FakeRedis
from src.application.services.base import ServiceFactory


# Тестовые настройки базы данных
test_settings = Settings(
    # DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
    SECRET_KEY="test-secret-key",
    WEBHOOK_SECRET_KEY="test-webhook-secret",
    REDIS_HOST="localhost",
    REDIS_PORT=6379,
    CACHE_TTL=300,
)


# Фикстура для тестовой базы данных
@pytest.fixture(scope="session")
async def engine():
    # Запускаем PostgreSQL-контейнер
    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as postgres:
        # Получаем URL подключения из контейнера
        database_url = postgres.get_connection_url()
        # Создаём движок
        engine = create_async_engine(database_url, echo=True)
        yield engine
        # После завершения тестов движок закроется автоматически
        engine.sync_engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine):
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)  # Создаем таблицы
        yield session
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # Удаляем таблицы после теста


# Фикстура для клиента FastAPI
@pytest.fixture(scope="function")
def client(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session  # type: ignore
    yield TestClient(app)
    app.dependency_overrides.clear()  # type: ignore


# Фикстура для мокового Redis
@pytest.fixture(scope="function")
async def fake_redis():
    redis = FakeRedis()
    yield redis
    await redis.close()


# Фикстура для ServiceFactory
@pytest.fixture(scope="function")
def service_factory(db_session):
    return ServiceFactory(db_session)
