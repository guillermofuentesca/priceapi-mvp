"""
Fixtures compartidos para tests
conftest.py es detectado automáticamente por pytest
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient

from main import app
from database import Base, get_db
from config import settings

# URL de base de datos de prueba (usa base de datos separada)
# Convertir URL a async (postgresql+asyncpg://)
TEST_DATABASE_URL = settings.async_database_url.replace("pricetracker_db", "pricetracker_test_db")
if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Engine de test
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests asíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture que proporciona una sesión de BD limpia para cada test
    Crea tablas al inicio y las elimina al final
    """
    # Crear todas las tablas
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Proporcionar sesión
    async with TestSessionLocal() as session:
        yield session
    
    # Limpiar tablas después del test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture que proporciona un cliente HTTP para testear endpoints
    Usa la base de datos de test
    """
    # Override de la dependency get_db
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Cliente HTTP asíncrono
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Limpiar override
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Datos de usuario de prueba"""
    return {
        "email": "test@test.com",
        "password": "testpass123",
        "full_name": "Test User",
        "username": "testuser"
    }


@pytest.fixture
def sample_product_data():
    """Datos de producto de prueba"""
    return {
        "external_id": "TEST123",
        "name": "Test Product",
        "description": "A test product",
        "category": "Test Category",
        "brand": "Test Brand",
        "product_url": "https://example.com/test",
        "country": "US",
        "currency": "USD",
        "current_price": 99.99,
        "original_price": 129.99
    }