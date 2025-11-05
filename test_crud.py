"""
Script de testing manual para CRUD operations
Ejecutar con: python test_crud.py
"""
import asyncio
from datetime import datetime
from database import AsyncSessionLocal
from crud import (
    create_product,
    get_product_by_asin,
    get_all_products,
    add_price_history,
    get_product_price_history,
    create_user,
    get_user_by_email,
    track_product_for_user,
    get_user_tracked_products,
    get_stats
)


async def test_crud():
    """Prueba todas las operaciones CRUD"""
    
    print("🧪 INICIANDO TESTS DE CRUD\n")
    
    async with AsyncSessionLocal() as db:
        
        # ========== TEST 1: Crear Producto ==========
        print("📦 TEST 1: Crear producto...")
        product_data = {
            "external_id": "B08N5WRWNW",
            "name": "iPhone 13 Pro",
            "description": "Smartphone Apple",
            "category": "Electronics",
            "brand": "Apple",
            "product_url": "https://amazon.com/dp/B08N5WRWNW",
            "country": "US",
            "currency": "USD",
            "current_price": 999.99,
            "original_price": 1199.99
        }
        
        product = await create_product(db, product_data)
        await db.commit()
        print(f"✅ Producto creado: ID={product.id}, Nombre={product.name}\n")
        
        # ========== TEST 2: Buscar Producto ==========
        print("🔍 TEST 2: Buscar producto por ASIN...")
        found = await get_product_by_asin(db, "B08N5WRWNW", "US")
        if found:
            print(f"✅ Producto encontrado: {found.name} - ${found.current_price}\n")
        else:
            print("❌ Producto no encontrado\n")
        
        # ========== TEST 3: Agregar Historial de Precio ==========
        print("📊 TEST 3: Agregar historial de precio...")
        price_record = await add_price_history(
            db,
            product_id=product.id,
            price=999.99,
            currency="USD",
            source="test"
        )
        await db.commit()
        print(f"✅ Precio registrado: ${price_record.price} en {price_record.scraped_at}\n")
        
        # ========== TEST 4: Obtener Historial ==========
        print("📈 TEST 4: Obtener historial de precios...")
        history = await get_product_price_history(db, product.id, limit=10)
        print(f"✅ Historial obtenido: {len(history)} registros\n")
        
        # ========== TEST 5: Crear Usuario ==========
        print("👤 TEST 5: Crear usuario...")
        user = await create_user(
            db,
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Usuario Test"
        )
        await db.commit()
        print(f"✅ Usuario creado: {user.email}\n")
        
        # ========== TEST 6: Buscar Usuario ==========
        print("🔍 TEST 6: Buscar usuario...")
        found_user = await get_user_by_email(db, "test@example.com")
        if found_user:
            print(f"✅ Usuario encontrado: {found_user.email}\n")
        
        # ========== TEST 7: Trackear Producto ==========
        print("⭐ TEST 7: Usuario trackea producto...")
        tracked = await track_product_for_user(
            db,
            user_id=user.id,
            product_id=product.id,
            alert_price=899.99
        )
        await db.commit()
        print(f"✅ Producto trackeado con alerta en ${tracked.alert_price}\n")
        
        # ========== TEST 8: Ver Productos Trackeados ==========
        print("📋 TEST 8: Ver productos trackeados del usuario...")
        tracked_products = await get_user_tracked_products(db, user.id)
        print(f"✅ Usuario trackea {len(tracked_products)} productos\n")
        
        # ========== TEST 9: Estadísticas ==========
        print("📊 TEST 9: Estadísticas generales...")
        stats = await get_stats(db)
        print("✅ Estadísticas:")
        print(f"   - Productos totales: {stats['total_products']}")
        print(f"   - Productos trackeados: {stats['tracked_products']}")
        print(f"   - Usuarios: {stats['total_users']}")
        print(f"   - Registros de precios: {stats['price_records']}\n")
        
        # ========== TEST 10: Listar Todos los Productos ==========
        print("📦 TEST 10: Listar todos los productos...")
        all_products = await get_all_products(db, limit=10)
        print(f"✅ Total productos en BD: {len(all_products)}\n")
        
        print("=" * 50)
        print("🎉 TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_crud())