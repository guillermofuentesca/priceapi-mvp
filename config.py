"""
Configuración central de la aplicación
Gestiona todas las variables de entorno y configuraciones
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings"""
    
    # ========== APLICACIÓN ==========
    APP_NAME: str = "Price Tracker API"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ========== API ==========
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ========== DATABASE ==========
    # PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://pricetracker_user:pricetracker_pass@localhost:5432/pricetracker_db",
        description="PostgreSQL connection string"
        )

    @property
    def async_database_url(self) -> str:
        """Convierte DATABASE_URL a formato asyncpg si es necesario"""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False  # Log SQL queries
    
    # ========== REDIS ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # Cache TTL (Time To Live) en segundos
    CACHE_TTL_PRICE: int = 300      # 5 minutos para precios
    CACHE_TTL_PRODUCT: int = 3600   # 1 hora para productos
    CACHE_TTL_SEARCH: int = 600     # 10 minutos para búsquedas
    
    # ========== RAINFOREST API ==========
    RAINFOREST_API_KEY: str = ""
    RAINFOREST_BASE_URL: str = "https://api.rainforestapi.com/request"
    RAINFOREST_RATE_LIMIT: int = 20  # requests por minuto (free tier)
    
    # ========== SEGURIDAD ==========
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    # ========== LOGGING ==========
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: str = "logs/app.log"
    
    # ========== RATE LIMITING ==========
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # ========== SCRAPING ==========
    MAX_CONCURRENT_SCRAPES: int = 5
    SCRAPE_TIMEOUT: int = 30  # segundos
    
    # ========== ALERTAS ==========
    ENABLE_EMAIL_ALERTS: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna la instancia de configuración (singleton)
    El decorador @lru_cache asegura que solo se cree una instancia
    """
    return Settings()


# Instancia global para importar
settings = get_settings()


# ========== HELPER FUNCTIONS ==========

def is_production() -> bool:
    """Verifica si estamos en entorno de producción"""
    return settings.ENVIRONMENT == "production"


def is_development() -> bool:
    """Verifica si estamos en entorno de desarrollo"""
    return settings.ENVIRONMENT == "development"


def get_redis_url() -> str:
    """Construye la URL de Redis con autenticación si existe"""
    if settings.REDIS_PASSWORD:
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    return settings.REDIS_URL


def get_database_url() -> str:
    """Retorna la URL de la base de datos"""
    return settings.DATABASE_URL


# ========== CONFIGURACIÓN DE LOGGING ==========

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "detailed",
            "filename": settings.LOG_FILE,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["console", "file"],
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
