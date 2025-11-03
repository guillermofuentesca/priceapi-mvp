from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PriceResponse(BaseModel):
    """Modelo de respuesta para precio de producto"""
    product_id: str = Field(..., description="ID único del producto")
    product_name: str = Field(..., description="Nombre del producto")
    country: str = Field(..., description="Código país (GT, MX, US, etc)")
    price: float = Field(..., gt=0, description="Precio actual")
    currency: str = Field(..., description="Moneda (USD, GTQ, etc)")
    discount_percentage: Optional[float] = Field(None, ge=0, le=100, description="% descuento si aplica")
    original_price: Optional[float] = Field(None, description="Precio original antes descuento")
    in_stock: bool = Field(..., description="Disponibilidad")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Cantidad disponible")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Calificación 0-5 estrellas")
    review_count: Optional[int] = Field(None, ge=0, description="Número de reseñas")
    last_updated: datetime = Field(..., description="Última actualización")
    source: str = Field(..., description="Fuente de datos")
    product_url: Optional[str] = Field(None, description="URL del producto")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "TERMO-STANLEY-001",
                "product_name": "Termo Stanley Classic 1L",
                "country": "GT",
                "price": 245.50,
                "currency": "GTQ",
                "discount_percentage": 15,
                "original_price": 289.00,
                "in_stock": True,
                "stock_quantity": 12,
                "rating": 4.7,
                "review_count": 2341,
                "last_updated": "2025-02-03T08:30:00Z",
                "source": "amazon_gt",
                "product_url": "https://amazon.com.gt/..."
            }
        }

class ProductSummary(BaseModel):
    """Modelo resumen de producto para listados"""
    product_id: str
    product_name: str
    category: str
    price_gt: Optional[float] = Field(None, description="Precio Guatemala")
    price_us: Optional[float] = Field(None, description="Precio USA")
    price_mx: Optional[float] = Field(None, description="Precio México")
    tracked_since: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "MONITOR-DELL-U2723DE",
                "product_name": "Monitor Dell UltraSharp 27 4K",
                "category": "electronics",
                "price_gt": 3250.00,
                "price_us": 429.99,
                "price_mx": 8500.00,
                "tracked_since": "2025-02-01T00:00:00Z"
            }
        }

class HealthResponse(BaseModel):
    """Modelo health check"""
    status: str
    version: str
    database: str
    api_calls_today: int
    uptime_seconds: Optional[int] = None