"""
HYBRID90-PRICEAPI-FEB25-V1
API de comparación de precios - Día 3
Integración con Rainforest API, Redis y PostgreSQL
"""
from fastapi import FastAPI, Query, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import logging.config

# Importaciones locales
from config import settings, LOGGING_CONFIG
from cache import cache, make_price_key, make_search_key
from database import get_db, init_db, close_db, check_db_connection
from database import Product as DBProduct, PriceHistory
from scraper import scraper, get_product_price, search_amazon_products, RainforestAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Configurar logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# ========== LIFECYCLE EVENTS ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación (startup/shutdown)"""
    # STARTUP
    logger.info("🚀 Iniciando Price Tracker API...")
    
    # Conectar a Redis
    await cache.connect()
    
    # Verificar conexión a PostgreSQL
    db_connected = await check_db_connection()
    if db_connected:
        # Crear tablas si no existen
        await init_db()
    else:
        logger.warning("⚠️ Continuando sin base de datos")
    
    logger.info(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} iniciado correctamente")
    logger.info(f"📍 Entorno: {settings.ENVIRONMENT}")
    logger.info(f"🌍 Servidor: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📚 Docs: http://{settings.HOST}:{settings.PORT}/docs")
    
    yield
    
    # SHUTDOWN
    logger.info("⏹️ Cerrando Price Tracker API...")
    await cache.disconnect()
    await close_db()
    logger.info("👋 Aplicación cerrada correctamente")


# ========== INICIALIZAR FASTAPI ==========

app = FastAPI(
    title=settings.APP_NAME,
    description="API REST para comparación de precios en tiempo real con Amazon",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== MODELOS PYDANTIC ==========

class ProductResponse(BaseModel):
    """Respuesta de producto"""
    id: Optional[int] = None
    external_id: str
    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    product_url: str
    country: str
    currency: str
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    in_stock: bool = True
    rating: Optional[float] = None
    ratings_total: Optional[int] = None
    is_tracked: bool = False
    
    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """Respuesta de historial de precios"""
    price: float
    currency: str
    scraped_at: datetime
    in_stock: bool
    
    class Config:
        from_attributes = True


class TrackRequest(BaseModel):
    """Request para trackear un producto"""
    product_id: str = Field(..., description="ASIN o ID del producto")
    country: str = Field("US", description="Código de país (US, MX, etc)")
    alert_price: Optional[float] = Field(None, description="Precio objetivo para alerta")


class TrackResponse(BaseModel):
    """Respuesta de tracking"""
    success: bool
    message: str
    product: ProductResponse


class HealthResponse(BaseModel):
    """Respuesta de health check"""
    status: str
    version: str
    timestamp: str
    services: dict


# ========== EXCEPTION HANDLERS ==========

@app.exception_handler(RainforestAPIError)
async def rainforest_exception_handler(request, exc: RainforestAPIError):
    """Maneja errores de Rainforest API"""
    logger.error(f"Rainforest API Error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Error al obtener datos de Amazon",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ========== ENDPOINTS ==========

@app.get("/", tags=["info"])
async def root():
    """Endpoint raíz - Información de la API"""
    return {
        "message": f"🚀 {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "price": "/price",
            "product": "/product/{asin}",
            "search": "/search",
            "history": "/history/{asin}",
            "track": "/track",
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["info"])
async def health_check():
    """Health check del servicio"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": "connected" if cache.is_connected else "disconnected",
            "database": "connected",  # TODO: implementar check real
            "scraper": "mock" if scraper.mock_mode else "active",
        }
    }


@app.get("/price", tags=["prices"])
async def get_price(
    asin: str = Query(..., description="Amazon ASIN del producto"),
    country: str = Query("US", description="Código país (US, MX, etc)"),
    force_refresh: bool = Query(False, description="Forzar actualización sin caché"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el precio actual de un producto de Amazon
    
    - Primero intenta obtener del caché (Redis)
    - Si no está en caché o force_refresh=True, hace scraping
    - Guarda en base de datos y caché
    """
    # Generar clave de caché
    cache_key = make_price_key(asin, country)
    
    # Intentar obtener del caché
    if not force_refresh:
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.info(f"💨 Precio obtenido del caché: {asin}")
            return {
                **cached_data,
                "source": "cache",
                "timestamp": datetime.now().isoformat()
            }
    
    # Hacer scraping con Rainforest API
    try:
        product_data = await get_product_price(asin, country)
        
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se pudo obtener información del producto {asin}"
            )
        
        # Guardar en base de datos
        try:
            # Buscar si el producto ya existe
            result = await db.execute(
                select(DBProduct).where(DBProduct.external_id == asin)
            )
            db_product = result.scalar_one_or_none()
            
            if db_product:
                # Actualizar producto existente
                db_product.current_price = product_data["current_price"]
                db_product.original_price = product_data["original_price"]
                db_product.last_scraped_at = datetime.now()
                logger.info(f"📝 Producto actualizado en BD: {asin}")
            else:
                # Crear nuevo producto
                db_product = DBProduct(
                    external_id=product_data["external_id"],
                    name=product_data["name"],
                    description=product_data.get("description"),
                    category=product_data.get("category"),
                    brand=product_data.get("brand"),
                    image_url=product_data.get("image_url"),
                    product_url=product_data["product_url"],
                    country=product_data["country"],
                    currency=product_data["currency"],
                    current_price=product_data["current_price"],
                    original_price=product_data.get("original_price"),
                    discount_percentage=product_data.get("discount_percentage"),
                    last_scraped_at=datetime.now()
                )
                db.add(db_product)
                logger.info(f"➕ Nuevo producto creado en BD: {asin}")
            
            await db.flush()
            
            # Guardar historial de precio
            price_history = PriceHistory(
                product_id=db_product.id,
                price=product_data["current_price"],
                original_price=product_data.get("original_price"),
                currency=product_data["currency"],
                in_stock=product_data.get("in_stock", True),
                source="rainforest" if not scraper.mock_mode else "mock"
            )
            db.add(price_history)
            await db.commit()
            
            logger.info(f"💾 Historial de precio guardado para {asin}")
            
        except Exception as e:
            logger.error(f"Error guardando en BD: {str(e)}")
            await db.rollback()
        
        # Guardar en caché
        await cache.set(cache_key, product_data, ttl=settings.CACHE_TTL_PRICE)
        
        return {
            **product_data,
            "source": "scraping",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo precio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo precio: {str(e)}"
        )


@app.get("/product/{asin}", response_model=ProductResponse, tags=["products"])
async def get_product(
    asin: str,
    country: str = Query("US", description="Código país"),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene información completa de un producto"""
    # Primero intentar obtener de BD
    result = await db.execute(
        select(DBProduct).where(
            DBProduct.external_id == asin,
            DBProduct.country == country
        )
    )
    db_product = result.scalar_one_or_none()
    
    if db_product:
        logger.info(f"📦 Producto obtenido de BD: {asin}")
        return ProductResponse.from_orm(db_product)
    
    # Si no está en BD, hacer scraping
    product_data = await get_product_price(asin, country)
    if not product_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {asin} no encontrado"
        )
    
    return ProductResponse(**product_data)


@app.get("/products", tags=["products"])
async def list_products(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    limit: int = Query(10, ge=1, le=100, description="Límite de resultados"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los productos de la base de datos
    
    Soporta paginación y filtro por categoría
    """
    from crud import get_all_products
    from sqlalchemy import select
    
    try:
        # Si hay filtro de categoría
        if category:
            result = await db.execute(
                select(Product)
                .where(Product.category.ilike(f"%{category}%"))
                .offset(skip)
                .limit(limit)
            )
            products = result.scalars().all()
        else:
            # Sin filtro, obtener todos
            products = await get_all_products(db, skip=skip, limit=limit)
        
        # Convertir a lista de diccionarios
        products_list = []
        for p in products:
            products_list.append({
                "id": p.id,
                "external_id": p.external_id,
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "country": p.country,
                "currency": p.currency,
                "current_price": p.current_price,
                "original_price": p.original_price,
                "discount_percentage": p.discount_percentage,
                "is_tracked": p.is_tracked,
                "image_url": p.image_url,
                "product_url": p.product_url
            })
        
        return {
            "products": products_list,
            "count": len(products_list),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listando productos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo productos: {str(e)}"
        )


@app.get("/search", tags=["search"])
async def search_products(
    q: str = Query(..., description="Término de búsqueda"),
    country: str = Query("US", description="Código país"),
    page: int = Query(1, ge=1, description="Número de página")
):
    """
    Busca productos en Amazon
    
    Los resultados se cachean por 10 minutos
    """
    # Verificar caché
    cache_key = make_search_key(q, country)
    cached_results = await cache.get(cache_key)
    
    if cached_results:
        logger.info(f"🔍 Resultados de búsqueda del caché: '{q}'")
        return {
            "query": q,
            "country": country,
            "page": page,
            "results": cached_results,
            "source": "cache",
            "timestamp": datetime.now().isoformat()
        }
    
    # Hacer búsqueda real
    try:
        results = await search_amazon_products(q, country)
        
        # Cachear resultados
        await cache.set(cache_key, results, ttl=settings.CACHE_TTL_SEARCH)
        
        return {
            "query": q,
            "country": country,
            "page": page,
            "results": results,
            "count": len(results),
            "source": "scraping",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en búsqueda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
        )


@app.get("/history/{asin}", response_model=List[PriceHistoryResponse], tags=["history"])
async def get_price_history(
    asin: str,
    country: str = Query("US", description="Código país"),
    limit: int = Query(30, ge=1, le=100, description="Número de registros"),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el historial de precios de un producto"""
    # Buscar producto
    result = await db.execute(
        select(DBProduct).where(
            DBProduct.external_id == asin,
            DBProduct.country == country
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {asin} no encontrado"
        )
    
    # Obtener historial
    history_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product.id)
        .order_by(PriceHistory.scraped_at.desc())
        .limit(limit)
    )
    history = history_result.scalars().all()
    
    return [PriceHistoryResponse.from_orm(h) for h in history]


@app.post("/track", response_model=TrackResponse, tags=["tracking"])
async def track_product(
    request: TrackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Agrega un producto a la lista de seguimiento
    
    - Hace scraping si no existe en BD
    - Marca el producto como trackeado
    - Configura alerta de precio si se especifica
    """
    asin = request.product_id
    country = request.country
    
    # Buscar producto en BD
    result = await db.execute(
        select(DBProduct).where(
            DBProduct.external_id == asin,
            DBProduct.country == country
        )
    )
    product = result.scalar_one_or_none()
    
    # Si no existe, crear con scraping
    if not product:
        product_data = await get_product_price(asin, country)
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se pudo obtener información del producto {asin}"
            )
        
        product = DBProduct(
            external_id=product_data["external_id"],
            name=product_data["name"],
            description=product_data.get("description"),
            category=product_data.get("category"),
            brand=product_data.get("brand"),
            image_url=product_data.get("image_url"),
            product_url=product_data["product_url"],
            country=product_data["country"],
            currency=product_data["currency"],
            current_price=product_data["current_price"],
            original_price=product_data.get("original_price"),
            is_tracked=True,
            tracking_count=1
        )
        db.add(product)
    else:
        # Actualizar producto existente
        product.is_tracked = True
        product.tracking_count = (product.tracking_count or 0) + 1
    
    await db.commit()
    await db.refresh(product)
    
    message = f"✅ Producto agregado a tracking"
    if request.alert_price:
        message += f". Te alertaremos si baja de ${request.alert_price}"
    
    return TrackResponse(
        success=True,
        message=message,
        product=ProductResponse.from_orm(product)
    )


# ========== ENDPOINTS DE ADMINISTRACIÓN ==========

@app.get("/admin/cache/clear", tags=["admin"])
async def clear_cache(pattern: str = Query("*", description="Patrón a limpiar")):
    """Limpia el caché (requiere autenticación en producción)"""
    if not cache.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis no está conectado"
        )
    
    deleted = await cache.clear_pattern(pattern)
    return {
        "success": True,
        "pattern": pattern,
        "deleted_keys": deleted,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/admin/stats", tags=["admin"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Estadísticas de la aplicación"""
    # Contar productos
    products_result = await db.execute(select(DBProduct))
    total_products = len(products_result.scalars().all())
    
    tracked_result = await db.execute(
        select(DBProduct).where(DBProduct.is_tracked == True)
    )
    tracked_products = len(tracked_result.scalars().all())
    
    return {
        "total_products": total_products,
        "tracked_products": tracked_products,
        "cache_connected": cache.is_connected,
        "scraper_mode": "mock" if scraper.mock_mode else "active",
        "timestamp": datetime.now().isoformat()
    }


# Para ejecutar directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
