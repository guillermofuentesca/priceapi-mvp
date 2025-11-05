from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

app = FastAPI(
    title="Price Tracker API",
    description="API para rastrear precios de productos",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== MODELOS ==========
class Product(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    country: str

class TrackRequest(BaseModel):
    url: str
    product_name: Optional[str] = None
    alert_price: Optional[float] = None
    country: str = "US"

class TrackResponse(BaseModel):
    success: bool
    product_id: int
    message: str
    tracked_url: str

# ========== ENDPOINTS ==========

@app.get("/", tags=["info"])
def read_root():
    """Endpoint raíz - Información de la API"""
    return {
        "message": "🚀 Price Tracker API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "price": "/price",
            "products": "/products",
            "track": "/track"
        }
    }

@app.get("/health", tags=["info"])
def health_check():
    """Health check del servicio"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "price-tracker-api"
    }

@app.get("/price", tags=["prices"])
def get_price(
    product_id: str = Query("iphone15", description="ID del producto"),
    country: str = Query("US", description="Código país (US, MX, etc)")
):
    """
    Obtiene el precio actual de un producto
    
    Por ahora retorna datos MOCK. En Día 3-4 conectaremos scraping real.
    """
    
    # DATOS MOCK
    mock_prices = {
        "iphone15": {
            "US": {"price": 999.99, "currency": "USD", "name": "iPhone 15 Pro"},
            "MX": {"price": 19999.00, "currency": "MXN", "name": "iPhone 15 Pro"}
        },
        "macbook": {
            "US": {"price": 1299.99, "currency": "USD", "name": "MacBook Air M2"},
            "MX": {"price": 24999.00, "currency": "MXN", "name": "MacBook Air M2"}
        },
        "airpods": {
            "US": {"price": 249.99, "currency": "USD", "name": "AirPods Pro"},
            "MX": {"price": 4999.00, "currency": "MXN", "name": "AirPods Pro"}
        }
    }
    
    product_data = mock_prices.get(product_id, mock_prices["iphone15"])
    price_data = product_data.get(country, product_data["US"])
    
    return {
        "product_id": product_id,
        "product_name": price_data["name"],
        "country": country,
        "price": price_data["price"],
        "currency": price_data["currency"],
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    }

@app.get("/products", tags=["products"])
def get_products(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    limit: int = Query(10, description="Límite de resultados")
):
    """
    Lista todos los productos disponibles
    
    Datos MOCK - En Semana 2 conectaremos base de datos real
    """
    
    mock_products = [
        {
            "id": "iphone15",
            "name": "iPhone 15 Pro",
            "category": "electronics",
            "price": 999.99,
            "currency": "USD",
            "is_tracked": True
        },
        {
            "id": "macbook",
            "name": "MacBook Air M2",
            "category": "electronics",
            "price": 1299.99,
            "currency": "USD",
            "is_tracked": True
        },
        {
            "id": "airpods",
            "name": "AirPods Pro",
            "category": "electronics",
            "price": 249.99,
            "currency": "USD",
            "is_tracked": False
        },
        {
            "id": "ps5",
            "name": "PlayStation 5",
            "category": "gaming",
            "price": 499.99,
            "currency": "USD",
            "is_tracked": False
        }
    ]
    
    # Filtrar por categoría si se especifica
    if category:
        mock_products = [p for p in mock_products if p["category"] == category]
    
    return mock_products[:limit]

@app.post("/track", response_model=TrackResponse, tags=["tracking"])
def track_product(request: TrackRequest):
    """
    Agrega un producto a tu lista de seguimiento
    
    En Semana 2 esto guardará en Supabase.
    Por ahora solo confirma que funciona.
    """
    import random
    
    new_id = random.randint(1000, 9999)
    
    alert_msg = f"Te alertaremos si baja de ${request.alert_price}" if request.alert_price else "Sin alerta de precio configurada"
    
    return {
        "success": True,
        "product_id": new_id,
        "message": f"✅ Producto agregado exitosamente. {alert_msg}",
        "tracked_url": request.url
    }

# Para ejecutar directamente con: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
