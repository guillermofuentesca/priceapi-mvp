"""
Sistema de caché usando Redis
Gestiona el almacenamiento temporal de precios y productos
"""
import json
import logging
from typing import Optional, Any, Union
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio import Redis
from config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Clase para gestionar el caché con Redis"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.is_connected: bool = False
    
    async def connect(self):
        """Conecta a Redis"""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("✅ Conexión a Redis establecida exitosamente")
        except Exception as e:
            self.is_connected = False
            logger.error(f"❌ Error conectando a Redis: {str(e)}")
            logger.warning("⚠️ La aplicación continuará sin caché")
    
    async def disconnect(self):
        """Desconecta de Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("🔌 Desconectado de Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché
        
        Args:
            key: Clave del valor a obtener
            
        Returns:
            El valor deserializado o None si no existe
        """
        if not self.is_connected:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"✅ Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"❌ Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo del caché: {str(e)}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Guarda un valor en el caché
        
        Args:
            key: Clave bajo la cual guardar
            value: Valor a guardar (será serializado a JSON)
            ttl: Tiempo de vida en segundos (None = sin expiración)
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not self.is_connected:
            return False
        
        try:
            serialized_value = json.dumps(value)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
            logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error guardando en caché: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Elimina una clave del caché
        
        Args:
            key: Clave a eliminar
            
        Returns:
            True si se eliminó, False en caso contrario
        """
        if not self.is_connected:
            return False
        
        try:
            await self.redis_client.delete(key)
            logger.debug(f"🗑️ Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando del caché: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Verifica si una clave existe en el caché"""
        if not self.is_connected:
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error verificando existencia: {str(e)}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Elimina todas las claves que coincidan con un patrón
        
        Args:
            pattern: Patrón a buscar (ej: "price:*")
            
        Returns:
            Número de claves eliminadas
        """
        if not self.is_connected:
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Eliminadas {deleted} claves con patrón: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error limpiando patrón: {str(e)}")
            return 0
    
    async def get_ttl(self, key: str) -> int:
        """
        Obtiene el TTL restante de una clave
        
        Returns:
            Segundos restantes, -1 si no tiene TTL, -2 si no existe
        """
        if not self.is_connected:
            return -2
        
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Error obteniendo TTL: {str(e)}")
            return -2
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Incrementa un contador en Redis
        Útil para rate limiting
        
        Returns:
            Valor después del incremento
        """
        if not self.is_connected:
            return 0
        
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementando contador: {str(e)}")
            return 0
    
    async def set_with_expiry(self, key: str, value: Any, seconds: int) -> bool:
        """Alias para set() con TTL obligatorio"""
        return await self.set(key, value, ttl=seconds)


# ========== FUNCIONES HELPER PARA CACHÉ ==========

def make_cache_key(*parts: str) -> str:
    """
    Crea una clave de caché consistente
    
    Ejemplo:
        make_cache_key("price", "B08N5WRWNW", "US") -> "price:B08N5WRWNW:US"
    """
    return ":".join(str(part) for part in parts)


def make_price_key(product_id: str, country: str) -> str:
    """Crea una clave para precios"""
    return make_cache_key("price", product_id, country)


def make_product_key(product_id: str) -> str:
    """Crea una clave para productos"""
    return make_cache_key("product", product_id)


def make_search_key(query: str, country: str) -> str:
    """Crea una clave para búsquedas"""
    return make_cache_key("search", query, country)


def make_rate_limit_key(identifier: str) -> str:
    """Crea una clave para rate limiting"""
    return make_cache_key("ratelimit", identifier)


# ========== INSTANCIA GLOBAL ==========

cache = RedisCache()


# ========== DECORADOR PARA CACHÉ ==========

def cached(ttl: int = 300, key_prefix: str = "cache"):
    """
    Decorador para cachear resultados de funciones
    
    Ejemplo:
        @cached(ttl=600, key_prefix="price")
        async def get_price(product_id: str):
            # ... lógica de scraping
            return price
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Construir clave de caché
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Intentar obtener del caché
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Ejecutar función y cachear resultado
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


# ========== RATE LIMITER ==========

class RateLimiter:
    """Rate limiter usando Redis"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """
        Verifica si una request está permitida
        
        Args:
            identifier: Identificador único (IP, user_id, etc)
            
        Returns:
            (permitido, requests_restantes)
        """
        if not cache.is_connected:
            return True, self.max_requests
        
        key = make_rate_limit_key(identifier)
        
        try:
            # Obtener contador actual
            current = await cache.redis_client.get(key)
            
            if current is None:
                # Primera request en esta ventana
                await cache.redis_client.setex(key, self.window_seconds, 1)
                return True, self.max_requests - 1
            
            current = int(current)
            
            if current >= self.max_requests:
                return False, 0
            
            # Incrementar contador
            new_value = await cache.redis_client.incr(key)
            remaining = max(0, self.max_requests - new_value)
            
            return True, remaining
            
        except Exception as e:
            logger.error(f"Error en rate limiter: {str(e)}")
            # En caso de error, permitir la request
            return True, self.max_requests


# Instancia global del rate limiter
rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_PER_MINUTE,
    window_seconds=60
)
