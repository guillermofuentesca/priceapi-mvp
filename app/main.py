from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="PriceAPI MVP",
    description="API de precios e-commerce",
    version="0.1.0"
)

# CORS (permite llamadas desde navegador)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENDPOINT 1: Health check
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "PriceAPI MVP v0.1.0",
        "endpoints": ["/", "/health", "/api/price/{product_id}"]
    }

# ENDPOINT 2: Health detallado
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "database": "not_connected",  # Después agregaremos
        "api_calls_today": 0  # Después agregaremos
    }

# ENDPOINT 3: Precio producto (simulado por ahora)
@app.get("/api/price/{product_id}")
def get_price(product_id: str, country: str = "GT"):
    # SIMULACIÓN - después conectaremos a scraping real
    mock_data = {
        "product_id": product_id,
        "country": country,
        "price": 99.99,
        "currency": "USD" if country == "US" else "GTQ",
        "in_stock": True,
        "last_updated": "2025-02-03T08:00:00Z",
        "source": "mock_data"
    }
    return mock_data

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)