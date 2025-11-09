"""
Configuración de base de datos PostgreSQL
Gestiona conexiones, modelos y operaciones CRUD
"""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)

# ========== CONFIGURACIÓN DEL ENGINE ==========

# Convertir URL de postgres:// a postgresql+asyncpg://
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Crear engine asíncrono
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DB_ECHO,  # Log SQL queries si DEBUG=True
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base para modelos
Base = declarative_base()


# ========== DEPENDENCY INJECTION ==========

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que proporciona una sesión de base de datos
    
    Uso en endpoints:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Error en transacción de BD: {str(e)}")
            raise
        finally:
            await session.close()


# ========== MODELOS DE BASE DE DATOS ==========

class Product(Base):
    """Modelo de Producto"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)  # ID de Amazon, etc
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    brand = Column(String(200), nullable=True)
    image_url = Column(Text, nullable=True)
    product_url = Column(Text, nullable=False)
    country = Column(String(5), nullable=False)  # US, MX, etc
    currency = Column(String(5), nullable=False)  # USD, MXN, etc
    
    # Precio actual (desnormalizado para performance)
    current_price = Column(Float, nullable=True)
    original_price = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=True)
    
    # Tracking
    is_tracked = Column(Boolean, default=False)
    tracking_count = Column(Integer, default=0)  # Cuántos usuarios lo siguen
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Product {self.name} - ${self.current_price}>"


class PriceHistory(Base):
    """Historial de precios de productos"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    currency = Column(String(5), nullable=False)
    
    # Disponibilidad
    in_stock = Column(Boolean, default=True)
    stock_status = Column(String(50), nullable=True)  # In Stock, Limited, Out of Stock
    
    # Metadata
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    source = Column(String(50), nullable=True)  # rainforest, manual, etc
    
    def __repr__(self):
        return f"<PriceHistory product_id={self.product_id} price=${self.price}>"


class User(Base):
    """Modelo de Usuario (para tracking personalizado)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Perfil
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Preferencias
    default_currency = Column(String(5), default="USD")
    default_country = Column(String(5), default="US")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User {self.email}>"


class TrackedProduct(Base):
    """Relación entre usuarios y productos que siguen"""
    __tablename__ = "tracked_products"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Configuración de alertas
    alert_price = Column(Float, nullable=True)  # Alertar si baja de este precio
    alert_enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_alerted = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<TrackedProduct user={self.user_id} product={self.product_id}>"


class PriceAlert(Base):
    """Log de alertas enviadas"""
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    alert_type = Column(String(50), nullable=False)  # price_drop, back_in_stock, etc
    old_price = Column(Float, nullable=True)
    new_price = Column(Float, nullable=True)
    
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_via = Column(String(50), default="email")  # email, push, sms
    
    def __repr__(self):
        return f"<PriceAlert {self.alert_type} user={self.user_id}>"
    
class APIKey(Base):
    """API Keys para developers"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # API Key
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)  # Nombre descriptivo
    
    # Plan y límites
    tier = Column(String(20), default="free")  # free, starter, pro, business, enterprise
    requests_per_month = Column(Integer, default=1000)
    requests_used = Column(Integer, default=0)
    
    # Estado
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<APIKey {self.name} - {self.tier}>"


class APIUsage(Base):
    """Log de uso de API keys"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)
    
    # Request info
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    
    # Metadata
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<APIUsage {self.method} {self.endpoint}>"


# ========== FUNCIONES DE INICIALIZACIÓN ==========

async def init_db():
    """Inicializa la base de datos creando todas las tablas"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Tablas de base de datos creadas exitosamente")
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {str(e)}")
        raise


async def drop_db():
    """CUIDADO: Elimina todas las tablas (solo para desarrollo)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("⚠️ Todas las tablas fueron eliminadas")
    except Exception as e:
        logger.error(f"❌ Error eliminando tablas: {str(e)}")
        raise


async def check_db_connection():
    """Verifica la conexión a la base de datos"""
    try:
        from sqlalchemy import text  # ✅ IMPORTAR text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))  # ✅ USAR text()
        logger.info("✅ Conexión a PostgreSQL exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {str(e)}")
        return False


# ========== CRUD HELPERS (Ejemplos) ==========

async def get_product_by_external_id(db: AsyncSession, external_id: str):
    """Obtiene un producto por su ID externo (Amazon ID, etc)"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Product).where(Product.external_id == external_id)
    )
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, product_data: dict):
    """Crea un nuevo producto"""
    product = Product(**product_data)
    db.add(product)
    await db.flush()
    return product


async def add_price_history(db: AsyncSession, product_id: int, price: float, **kwargs):
    """Agrega un registro al historial de precios"""
    price_record = PriceHistory(
        product_id=product_id,
        price=price,
        **kwargs
    )
    db.add(price_record)
    await db.flush()
    return price_record


async def get_product_price_history(
    db: AsyncSession, 
    product_id: int, 
    limit: int = 30
):
    """Obtiene el historial de precios de un producto"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.scraped_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ========== CLEANUP ==========

async def close_db():
    """Cierra las conexiones de la base de datos"""
    await engine.dispose()
    logger.info("🔌 Conexiones de base de datos cerradas")
