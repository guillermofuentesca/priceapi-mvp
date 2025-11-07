"""
Tests de integración para endpoints HTTP
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.endpoints
async def test_root_endpoint(client: AsyncClient):
    """Test endpoint raíz"""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.integration
@pytest.mark.endpoints
async def test_health_check(client: AsyncClient):
    """Test health check"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.integration
@pytest.mark.endpoints
async def test_register_user(client: AsyncClient):
    """Test registro de usuario"""
    user_data = {
        "email": "test@endpoint.com",
        "password": "testpass",
        "full_name": "Test User"
    }
    
    response = await client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@endpoint.com"
    assert "id" in data


@pytest.mark.integration
@pytest.mark.endpoints
async def test_login(client: AsyncClient):
    """Test login"""
    # Primero registrar usuario
    await client.post("/auth/register", json={
        "email": "login@test.com",
        "password": "testpass"
    })
    
    # Login
    response = await client.post("/auth/login", data={
        "username": "login@test.com",
        "password": "testpass"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
@pytest.mark.endpoints
async def test_get_me_unauthorized(client: AsyncClient):
    """Test acceso sin token"""
    response = await client.get("/auth/me")
    
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.endpoints
async def test_get_me_authorized(client: AsyncClient):
    """Test obtener usuario actual"""
    # Registrar y hacer login
    await client.post("/auth/register", json={
        "email": "me@test.com",
        "password": "testpass",
        "full_name": "Me User"
    })
    
    login_response = await client.post("/auth/login", data={
        "username": "me@test.com",
        "password": "testpass"
    })
    token = login_response.json()["access_token"]
    
    # Obtener perfil
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@test.com"
    assert data["full_name"] == "Me User"


@pytest.mark.integration
@pytest.mark.endpoints
async def test_get_products(client: AsyncClient):
    """Test listar productos"""
    response = await client.get("/products")
    
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert isinstance(data["products"], list)