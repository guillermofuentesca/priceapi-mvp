# PriceAPI MVP

API de precios e-commerce para comparación multi-plataforma.

## Status
🚧 **MVP en construcción** - Día 1/90

## Objetivo
Proveer datos de precios actualizados de productos en tiempo real para desarrolladores, apps de comparación y consumidores.

## Stack
- **Backend:** FastAPI (Python 3.10)
- **Database:** Supabase (próximamente)
- **Deploy:** Railway.app (próximamente)
- **Scraping:** Beautiful Soup + Apify (próximamente)

## Instalación Local

```bash
# Clonar repo
git clone git@github.com:guillermofuentesca/priceapi-mvp.git
cd priceapi-mvp

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Correr servidor
python -m app.main

# API corriendo en: http://localhost:8000
# Docs: http://localhost:8000/docs