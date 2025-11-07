from fastapi import FastAPI, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import uvicorn

# Importar modelos
from app.models.product import PriceResponse, ProductSummary, HealthResponse

app = FastAPI(
    title="PriceAPI MVP",
    description="API de precios e-commerce multi-plataforma",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENDPOINT 1: Root
@app.get("/", tags=["General"])
def read_root():
    """Endpoint raíz - información general API"""
    return {
        "name": "PriceAPI MVP",
        "status": "online",
        "version": "0.1.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "price": "/api/price/{product_id}",
            "products": "/api/products"
        },
        "author": "Guillermo Fuentes",
        "repository": "github.com/guillermofuentesca/priceapi-mvp"
    }

# ENDPOINT 2: Health check mejorado
@app.get("/health", response_model=HealthResponse, tags=["General"])
def health_check():
    """Health check detallado del sistema"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        database="not_connected",  # Próximamente Supabase
        api_calls_today=0,  # Próximamente analytics real
        uptime_seconds=None
    )

# ENDPOINT 3: Precio producto mejorado
@app.get(
    "/api/price/{product_id}", 
    response_model=PriceResponse,
    tags=["Prices"],
    summary="Obtener precio de producto específico",
    description="Retorna precio actual, histórico y metadata de producto"
)
def get_price(
    product_id: str = Path(..., description="ID único del producto", example="TERMO-STANLEY-001"),
    country: str = Query("GT", description="Código país ISO", regex="^[A-Z]{2}$", example="GT")
):
    """
    Obtiene precio actualizado de un producto específico.
    
    - **product_id**: Identificador único del producto
    - **country**: Código país de 2 letras (GT, MX, US, etc)
    
    Retorna información completa incluyendo descuentos, stock y ratings.
    """
    
    # DATOS MOCK MEJORADOS (después conectaremos scraping real)
    mock_products = {
        "TERMO-STANLEY-001": {
            "product_name": "Termo Stanley Classic 1L",
            "price_gt": 245.50,
            "price_us": 32.99,
            "rating": 4.7,
            "reviews": 2341
        },
        "MONITOR-DELL-U2723DE": {
            "product_name": "Monitor Dell UltraSharp 27 4K",
            "price_gt": 3250.00,
            "price_us": 429.99,
            "rating": 4.8,
            "reviews": 1823
        },
        "LAPTOP-THINKPAD-T14": {
            "product_name": "Lenovo ThinkPad T14 Gen 3",
            "price_gt": 12500.00,
            "price_us": 1299.99,
            "rating": 4.6,
            "reviews": 892
        }
    }
    
    # Buscar producto o usar default
    product_data = mock_products.get(
        product_id, 
        {
            "product_name": f"Producto {product_id}",
            "price_gt": 99.99,
            "price_us": 12.99,
            "rating": 4.5,
            "reviews": 100
        }
    )
    
    # Seleccionar precio según país
    price_map = {
        "GT": product_data.get("price_gt", 99.99),
        "US": product_data.get("price_us", 12.99),
        "MX": product_data.get("price_gt", 99.99) * 0.7,  # Aproximado
    }
    
    currency_map = {
        "GT": "GTQ",
        "US": "USD",
        "MX": "MXN"
    }
    
    current_price = price_map.get(country, 99.99)
    original_price = current_price * 1.15  # Simular 15% descuento
    
    return PriceResponse(
        product_id=product_id,
        product_name=product_data["product_name"],
        country=country,
        price=round(current_price, 2),
        currency=currency_map.get(country, "USD"),
        discount_percentage=15.0,
        original_price=round(original_price, 2),
        in_stock=True,
        stock_quantity=12,
        rating=product_data.get("rating", 4.5),
        review_count=product_data.get("reviews", 100),
        last_updated=datetime.now(),
        source="mock_database_v1",
        product_url=f"https://example.com/product/{product_id}"
    )

# ENDPOINT 4: Lista de productos (NUEVO)
@app.get(
    "/api/products",
    response_model=List[ProductSummary],
    tags=["Products"],
    summary="Listar productos disponibles",
    description="Retorna catálogo de productos trackeados con precios múltiples países"
)
def list_products(
    category: str = Query(None, description="Filtrar por categoría", example="electronics"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de resultados")
):
    """
    Lista productos disponibles en el sistema.
    
    Filtra por categoría y limita resultados.
    Útil para explorar catálogo antes de consultar precios específicos.
    """
    
    # CATÁLOGO MOCK
    all_products = [
        ProductSummary(
            product_id="TERMO-STANLEY-001",
            product_name="Termo Stanley Classic 1L",
            category="home",
            price_gt=245.50,
            price_us=32.99,
            price_mx=650.00,
            tracked_since=datetime(2025, 2, 1)
        ),
        ProductSummary(
            product_id="MONITOR-DELL-U2723DE",
            product_name="Monitor Dell UltraSharp 27 4K",
            category="electronics",
            price_gt=3250.00,
            price_us=429.99,
            price_mx=8500.00,
            tracked_since=datetime(2025, 2, 1)
        ),
        ProductSummary(
            product_id="LAPTOP-THINKPAD-T14",
            product_name="Lenovo ThinkPad T14 Gen 3",
            category="electronics",
            price_gt=12500.00,
            price_us=1299.99,
            price_mx=25000.00,
            tracked_since=datetime(2025, 1, 28)
        ),
        ProductSummary(
            product_id="CAFETERA-NINJA-CFP301",
            product_name="Cafetera Ninja DualBrew Pro",
            category="home",
            price_gt=890.00,
            price_us=119.99,
            price_mx=2200.00,
            tracked_since=datetime(2025, 1, 25)
        ),
        ProductSummary(
            product_id="AUDIFONOS-SONY-WH1000XM5",
            product_name="Sony WH-1000XM5 Noise Cancelling",
            category="electronics",
            price_gt=2850.00,
            price_us=379.99,
            price_mx=7200.00,
            tracked_since=datetime(2025, 1, 20)
        )
    ]
    
    # Filtrar por categoría si se especifica
    if category:
        filtered = [p for p in all_products if p.category == category]
    else:
        filtered = all_products
    
    # Limitar resultados
    return filtered[:limit]

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)