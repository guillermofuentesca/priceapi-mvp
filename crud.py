"""
CRUD Operations para Price Tracker API
Create, Read, Update, Delete para cada modelo
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from datetime import datetime
import secrets 

from database import Product, PriceHistory, User, TrackedProduct, PriceAlert


# ========== PRODUCTS CRUD ==========

async def create_product(db: AsyncSession, product_data: dict) -> Product:
    """Crea un nuevo producto"""
    product = Product(**product_data)
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    """Obtiene un producto por ID"""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def get_product_by_asin(db: AsyncSession, asin: str, country: str = "US") -> Optional[Product]:
    """Obtiene un producto por ASIN y país"""
    result = await db.execute(
        select(Product).where(
            Product.external_id == asin,
            Product.country == country
        )
    )
    return result.scalar_one_or_none()


async def get_all_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Product]:
    """Lista todos los productos con paginación"""
    result = await db.execute(
        select(Product)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_tracked_products(db: AsyncSession) -> List[Product]:
    """Obtiene solo productos que están siendo trackeados"""
    result = await db.execute(
        select(Product).where(Product.is_tracked == True)
    )
    return result.scalars().all()


async def update_product_price(
    db: AsyncSession,
    product_id: int,
    new_price: float,
    original_price: Optional[float] = None
) -> Optional[Product]:
    """Actualiza el precio de un producto"""
    result = await db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(
            current_price=new_price,
            original_price=original_price,
            last_scraped_at=datetime.now()
        )
        .returning(Product)
    )
    await db.commit()
    return result.scalar_one_or_none()


async def delete_product(db: AsyncSession, product_id: int) -> bool:
    """Elimina un producto"""
    result = await db.execute(
        delete(Product).where(Product.id == product_id)
    )
    await db.commit()
    return result.rowcount > 0


# ========== PRICE HISTORY CRUD ==========

async def add_price_history(
    db: AsyncSession,
    product_id: int,
    price: float,
    currency: str = "USD",
    in_stock: bool = True,
    source: str = "rainforest"
) -> PriceHistory:
    """Agrega un registro al historial de precios"""
    price_record = PriceHistory(
        product_id=product_id,
        price=price,
        currency=currency,
        in_stock=in_stock,
        source=source
    )
    db.add(price_record)
    await db.flush()
    await db.refresh(price_record)
    return price_record


async def get_product_price_history(
    db: AsyncSession,
    product_id: int,
    limit: int = 30
) -> List[PriceHistory]:
    """Obtiene el historial de precios de un producto"""
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.scraped_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_latest_price(db: AsyncSession, product_id: int) -> Optional[PriceHistory]:
    """Obtiene el precio más reciente de un producto"""
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.scraped_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ========== USERS CRUD ==========

async def create_user(db: AsyncSession, email: str, hashed_password: str, **kwargs) -> User:
    """Crea un nuevo usuario"""
    user = User(
        email=email,
        hashed_password=hashed_password,
        **kwargs
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Obtiene un usuario por email"""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Obtiene un usuario por ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


# ========== TRACKED PRODUCTS CRUD ==========

async def track_product_for_user(
    db: AsyncSession,
    user_id: int,
    product_id: int,
    alert_price: Optional[float] = None
) -> TrackedProduct:
    """Usuario empieza a trackear un producto"""
    tracked = TrackedProduct(
        user_id=user_id,
        product_id=product_id,
        alert_price=alert_price,
        alert_enabled=True if alert_price else False
    )
    db.add(tracked)
    
    # Incrementar contador de tracking en producto
    await db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(
            is_tracked=True,
            tracking_count=Product.tracking_count + 1
        )
    )
    
    await db.flush()
    await db.refresh(tracked)
    return tracked


async def untrack_product_for_user(
    db: AsyncSession,
    user_id: int,
    product_id: int
) -> bool:
    """Usuario deja de trackear un producto"""
    result = await db.execute(
        delete(TrackedProduct).where(
            TrackedProduct.user_id == user_id,
            TrackedProduct.product_id == product_id
        )
    )
    
    # Decrementar contador si se eliminó
    if result.rowcount > 0:
        await db.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(tracking_count=Product.tracking_count - 1)
        )
    
    await db.commit()
    return result.rowcount > 0


async def get_user_tracked_products(
    db: AsyncSession,
    user_id: int
) -> List[TrackedProduct]:
    """Obtiene todos los productos que un usuario trackea"""
    result = await db.execute(
        select(TrackedProduct)
        .where(TrackedProduct.user_id == user_id)
    )
    return result.scalars().all()


# ========== PRICE ALERTS CRUD ==========

async def create_price_alert(
    db: AsyncSession,
    user_id: int,
    product_id: int,
    alert_type: str,
    old_price: Optional[float] = None,
    new_price: Optional[float] = None
) -> PriceAlert:
    """Crea un registro de alerta enviada"""
    alert = PriceAlert(
        user_id=user_id,
        product_id=product_id,
        alert_type=alert_type,
        old_price=old_price,
        new_price=new_price,
        sent_via="email"
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


async def get_user_alerts(
    db: AsyncSession,
    user_id: int,
    limit: int = 50
) -> List[PriceAlert]:
    """Obtiene el historial de alertas de un usuario"""
    result = await db.execute(
        select(PriceAlert)
        .where(PriceAlert.user_id == user_id)
        .order_by(PriceAlert.sent_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ========== ESTADÍSTICAS ==========

async def get_stats(db: AsyncSession) -> dict:
    """Obtiene estadísticas generales de la aplicación"""
    # Total productos
    total_products = await db.execute(select(Product))
    total_products_count = len(total_products.scalars().all())
    
    # Productos trackeados
    tracked = await db.execute(
        select(Product).where(Product.is_tracked == True)
    )
    tracked_count = len(tracked.scalars().all())
    
    # Total usuarios
    users = await db.execute(select(User))
    users_count = len(users.scalars().all())
    
    # Total registros de precio
    history = await db.execute(select(PriceHistory))
    history_count = len(history.scalars().all())
    
    return {
        "total_products": total_products_count,
        "tracked_products": tracked_count,
        "total_users": users_count,
        "price_records": history_count
    }

# ========== API KEYS CRUD ==========

import secrets
from database import APIKey, APIUsage


async def generate_api_key() -> str:
    """Genera una API key única y segura"""
    return f"hybrid90_{secrets.token_urlsafe(32)}"


async def create_api_key(
    db: AsyncSession,
    user_id: int,
    name: str,
    tier: str = "free"
) -> APIKey:
    """
    Crea una nueva API key para un usuario
    
    Tiers disponibles:
    - free: 1,000 req/mes
    - starter: 10,000 req/mes
    - pro: 100,000 req/mes
    - business: 500,000 req/mes
    - enterprise: unlimited
    """
    # Límites por tier
    # Límites actualizados según estrategia v2.1
    tier_limits = {
        "free": 500,              # Reducido de 1000
        "starter": 10000,         # Igual
        "professional": 50000,     # NUEVO tier
        "business": 250000,       # Ajustado de 500k
        "enterprise": 999999999   # Unlimited
    }
    
    # Generar key única
    key = await generate_api_key()
    
    api_key = APIKey(
        user_id=user_id,
        key=key,
        name=name,
        tier=tier,
        requests_per_month=tier_limits.get(tier, 1000),
        is_active=True
    )
    
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)
    return api_key


async def get_api_key_by_key(db: AsyncSession, key: str) -> Optional[APIKey]:
    """Obtiene una API key por su valor"""
    result = await db.execute(
        select(APIKey).where(APIKey.key == key, APIKey.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_user_api_keys(db: AsyncSession, user_id: int) -> List[APIKey]:
    """Obtiene todas las API keys de un usuario"""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == user_id)
        .order_by(APIKey.created_at.desc())
    )
    return result.scalars().all()


async def delete_api_key(db: AsyncSession, key_id: int, user_id: int) -> bool:
    """Elimina una API key (solo si pertenece al usuario)"""
    result = await db.execute(
        delete(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        )
    )
    await db.commit()
    return result.rowcount > 0


async def log_api_usage(
    db: AsyncSession,
    api_key_id: int,
    endpoint: str,
    method: str,
    status_code: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> APIUsage:
    """Registra el uso de una API key"""
    usage = APIUsage(
        api_key_id=api_key_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(usage)
    
    # Incrementar contador de uso
    await db.execute(
        update(APIKey)
        .where(APIKey.id == api_key_id)
        .values(
            requests_used=APIKey.requests_used + 1,
            last_used_at=datetime.now()
        )
    )
    
    await db.flush()
    return usage


async def check_rate_limit(db: AsyncSession, api_key: APIKey) -> tuple[bool, int]:
    """Verifica si una API key ha excedido su límite"""
    remaining = api_key.requests_per_month - api_key.requests_used
    
    if api_key.requests_used >= api_key.requests_per_month:
        return False, 0
    
    return True, remaining


async def reset_monthly_usage(db: AsyncSession):
    """
    Resetea el contador de uso mensual de todas las API keys
    (Ejecutar con cron job el primer día de cada mes)
    """
    await db.execute(
        update(APIKey).values(requests_used=0)
    )
    await db.commit()