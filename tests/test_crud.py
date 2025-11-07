"""
Tests unitarios para operaciones CRUD
"""
import pytest
from crud import (
    create_product,
    get_product_by_asin,
    get_all_products,
    create_user,
    get_user_by_email,
    add_price_history,
    get_product_price_history,
    track_product_for_user,
    get_user_tracked_products
)


@pytest.mark.unit
@pytest.mark.crud
async def test_create_product(db_session, sample_product_data):
    """Test crear producto"""
    product = await create_product(db_session, sample_product_data)
    await db_session.commit()
    
    assert product.id is not None
    assert product.external_id == "TEST123"
    assert product.name == "Test Product"
    assert product.current_price == 99.99


@pytest.mark.unit
@pytest.mark.crud
async def test_get_product_by_asin(db_session, sample_product_data):
    """Test buscar producto por ASIN"""
    # Crear producto
    await create_product(db_session, sample_product_data)
    await db_session.commit()
    
    # Buscar producto
    found = await get_product_by_asin(db_session, "TEST123", "US")
    
    assert found is not None
    assert found.external_id == "TEST123"


@pytest.mark.unit
@pytest.mark.crud
async def test_get_product_not_found(db_session):
    """Test producto no encontrado"""
    found = await get_product_by_asin(db_session, "NOEXISTE", "US")
    assert found is None


@pytest.mark.unit
@pytest.mark.crud
async def test_create_user(db_session, sample_user_data):
    """Test crear usuario"""
    from auth import get_password_hash
    
    user = await create_user(
        db_session,
        email=sample_user_data["email"],
        hashed_password=get_password_hash(sample_user_data["password"]),
        full_name=sample_user_data["full_name"]
    )
    await db_session.commit()
    
    assert user.id is not None
    assert user.email == "test@test.com"
    assert user.full_name == "Test User"


@pytest.mark.unit
@pytest.mark.crud
async def test_get_user_by_email(db_session, sample_user_data):
    """Test buscar usuario por email"""
    from auth import get_password_hash
    
    # Crear usuario
    await create_user(
        db_session,
        email=sample_user_data["email"],
        hashed_password=get_password_hash(sample_user_data["password"])
    )
    await db_session.commit()
    
    # Buscar usuario
    found = await get_user_by_email(db_session, "test@test.com")
    
    assert found is not None
    assert found.email == "test@test.com"


@pytest.mark.unit
@pytest.mark.crud
async def test_add_price_history(db_session, sample_product_data):
    """Test agregar historial de precio"""
    # Crear producto
    product = await create_product(db_session, sample_product_data)
    await db_session.commit()
    
    # Agregar historial
    history = await add_price_history(
        db_session,
        product_id=product.id,
        price=89.99,
        currency="USD"
    )
    await db_session.commit()
    
    assert history.id is not None
    assert history.price == 89.99
    assert history.product_id == product.id


@pytest.mark.unit
@pytest.mark.crud
async def test_get_price_history(db_session, sample_product_data):
    """Test obtener historial de precios"""
    # Crear producto
    product = await create_product(db_session, sample_product_data)
    await db_session.commit()
    
    # Agregar varios precios
    for price in [99.99, 89.99, 79.99]:
        await add_price_history(db_session, product.id, price, "USD")
    await db_session.commit()
    
    # Obtener historial
    history = await get_product_price_history(db_session, product.id, limit=10)
    
    assert len(history) == 3
    prices = [h.price for h in history]
    assert 99.99 in prices
    assert 89.99 in prices
    assert 79.99 in prices


@pytest.mark.unit
@pytest.mark.crud
async def test_track_product(db_session, sample_user_data, sample_product_data):
    """Test trackear producto"""
    from auth import get_password_hash
    
    # Crear usuario y producto
    user = await create_user(
        db_session,
        email=sample_user_data["email"],
        hashed_password=get_password_hash(sample_user_data["password"])
    )
    product = await create_product(db_session, sample_product_data)
    await db_session.commit()
    
    # Trackear producto
    tracked = await track_product_for_user(
        db_session,
        user_id=user.id,
        product_id=product.id,
        alert_price=79.99
    )
    await db_session.commit()
    
    assert tracked.id is not None
    assert tracked.user_id == user.id
    assert tracked.product_id == product.id
    assert tracked.alert_price == 79.99