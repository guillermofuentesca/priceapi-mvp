"""
Seeds - Datos de prueba para desarrollo
Ejecutar con: python seeds.py
"""
import asyncio
from database import AsyncSessionLocal
from crud import create_product, add_price_history
from datetime import datetime, timedelta
import random


async def seed_database():
    """Poblar base de datos con datos de prueba"""
    
    print("🌱 INICIANDO SEEDS DE DATOS\n")
    
    async with AsyncSessionLocal() as db:
        
        # ========== PRODUCTOS MOCK ==========
        products_data = [
            {
                "external_id": "B09V3KXJPB",
                "name": "MacBook Air M2 13-inch",
                "description": "Laptop Apple con chip M2, 8GB RAM, 256GB SSD",
                "category": "Electronics > Computers",
                "brand": "Apple",
                "image_url": "https://via.placeholder.com/300?text=MacBook+Air+M2",
                "product_url": "https://amazon.com/dp/B09V3KXJPB",
                "country": "US",
                "currency": "USD",
                "current_price": 1199.00,
                "original_price": 1299.00,
                "discount_percentage": 7.7,
                "is_tracked": True
            },
            {
                "external_id": "B0BSHF7WHW",
                "name": "AirPods Pro 2nd Generation",
                "description": "Auriculares con cancelación de ruido activa",
                "category": "Electronics > Audio",
                "brand": "Apple",
                "image_url": "https://via.placeholder.com/300?text=AirPods+Pro",
                "product_url": "https://amazon.com/dp/B0BSHF7WHW",
                "country": "US",
                "currency": "USD",
                "current_price": 249.99,
                "original_price": 249.99,
                "is_tracked": False
            },
            {
                "external_id": "B0CX23V2ZK",
                "name": "PlayStation 5 Slim",
                "description": "Consola de videojuegos Sony PS5",
                "category": "Video Games > Consoles",
                "brand": "Sony",
                "image_url": "https://via.placeholder.com/300?text=PS5",
                "product_url": "https://amazon.com/dp/B0CX23V2ZK",
                "country": "US",
                "currency": "USD",
                "current_price": 499.99,
                "original_price": 499.99,
                "is_tracked": True
            },
            {
                "external_id": "B0D1XD1ZV3",
                "name": "Samsung Galaxy S24 Ultra",
                "description": "Smartphone Samsung con S Pen, 256GB",
                "category": "Electronics > Cell Phones",
                "brand": "Samsung",
                "image_url": "https://via.placeholder.com/300?text=Galaxy+S24",
                "product_url": "https://amazon.com/dp/B0D1XD1ZV3",
                "country": "US",
                "currency": "USD",
                "current_price": 1199.99,
                "original_price": 1299.99,
                "discount_percentage": 7.7,
                "is_tracked": False
            },
            {
                "external_id": "B0BDJ2L26Y",
                "name": "Apple Watch Series 9",
                "description": "Smartwatch con GPS, 45mm",
                "category": "Electronics > Wearables",
                "brand": "Apple",
                "image_url": "https://via.placeholder.com/300?text=Apple+Watch",
                "product_url": "https://amazon.com/dp/B0BDJ2L26Y",
                "country": "US",
                "currency": "USD",
                "current_price": 429.00,
                "original_price": 429.00,
                "is_tracked": True
            }
        ]
        
        print("📦 Creando productos...")
        created_products = []
        
        for product_data in products_data:
            product = await create_product(db, product_data)
            created_products.append(product)
            print(f"   ✅ {product.name} - ${product.current_price}")
        
        await db.commit()
        print(f"\n✅ {len(created_products)} productos creados\n")
        
        # ========== HISTORIAL DE PRECIOS ==========
        print("📊 Generando historial de precios (últimos 30 días)...")
        
        for product in created_products:
            # Generar precios aleatorios de los últimos 30 días
            base_price = product.current_price
            
            for days_ago in range(30, 0, -1):
                # Variación aleatoria del precio (-10% a +10%)
                variation = random.uniform(-0.10, 0.10)
                price = base_price * (1 + variation)
                price = round(price, 2)
                
                # Fecha del registro
                # (simulamos que fue scrapeado días atrás)
                
                await add_price_history(
                    db,
                    product_id=product.id,
                    price=price,
                    currency=product.currency,
                    in_stock=random.choice([True, True, True, False]),  # 75% en stock
                    source="seed"
                )
            
            print(f"   ✅ {product.name}: 30 registros")
        
        await db.commit()
        print(f"\n✅ Historial de {30 * len(created_products)} registros creado\n")
        
        # ========== ESTADÍSTICAS FINALES ==========
        print("=" * 60)
        print("📊 SEEDS COMPLETADOS")
        print("=" * 60)
        print(f"✅ Productos: {len(created_products)}")
        print(f"✅ Registros de precios: {30 * len(created_products)}")
        print(f"✅ Productos trackeados: {sum(1 for p in created_products if p.is_tracked)}")
        print("=" * 60)
        print("\n🎉 Base de datos lista para desarrollo!\n")


if __name__ == "__main__":
    asyncio.run(seed_database())