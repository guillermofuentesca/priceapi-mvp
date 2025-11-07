"""
Tests unitarios para sistema de autenticación
"""
import pytest
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    authenticate_user,
    register_user,
    UserCreate
)
from crud import create_user


@pytest.mark.unit
@pytest.mark.auth
def test_password_hash():
    """Test hashear password"""
    password = "mypassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert len(hashed) > 20


@pytest.mark.unit
@pytest.mark.auth
def test_verify_password():
    """Test verificar password"""
    password = "mypassword123"
    hashed = get_password_hash(password)
    
    # Password correcto
    assert verify_password(password, hashed) is True
    
    # Password incorrecto
    assert verify_password("wrongpassword", hashed) is False


@pytest.mark.unit
@pytest.mark.auth
def test_create_access_token():
    """Test crear token JWT"""
    data = {"sub": "user@test.com"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50


@pytest.mark.unit
@pytest.mark.auth
def test_decode_access_token():
    """Test decodificar token JWT"""
    email = "user@test.com"
    token = create_access_token({"sub": email})
    
    decoded_email = decode_access_token(token)
    
    assert decoded_email == email


@pytest.mark.unit
@pytest.mark.auth
def test_decode_invalid_token():
    """Test decodificar token inválido"""
    invalid_token = "invalid.token.here"
    
    result = decode_access_token(invalid_token)
    
    assert result is None


@pytest.mark.unit
@pytest.mark.auth
async def test_authenticate_user_success(db_session):
    """Test autenticar usuario exitoso"""
    # Crear usuario
    password = "testpass123"
    hashed = get_password_hash(password)
    user = await create_user(
        db_session,
        email="auth@test.com",
        hashed_password=hashed,
        full_name="Auth Test"
    )
    await db_session.commit()
    
    # Autenticar
    authenticated = await authenticate_user(db_session, "auth@test.com", password)
    
    assert authenticated is not None
    assert authenticated.id == user.id
    assert authenticated.email == "auth@test.com"


@pytest.mark.unit
@pytest.mark.auth
async def test_authenticate_user_wrong_password(db_session):
    """Test autenticar con password incorrecto"""
    # Crear usuario
    hashed = get_password_hash("testpass123")
    await create_user(
        db_session,
        email="auth@test.com",
        hashed_password=hashed
    )
    await db_session.commit()
    
    # Autenticar con password incorrecto
    authenticated = await authenticate_user(db_session, "auth@test.com", "wrongpass")
    
    assert authenticated is None


@pytest.mark.unit
@pytest.mark.auth
async def test_authenticate_user_not_found(db_session):
    """Test autenticar usuario inexistente"""
    authenticated = await authenticate_user(db_session, "notfound@test.com", "anypass")
    
    assert authenticated is None


@pytest.mark.unit
@pytest.mark.auth
async def test_register_user(db_session):
    """Test registrar nuevo usuario"""
    user_data = UserCreate(
        email="newuser@test.com",
        password="newpass123",
        full_name="New User"
    )
    
    user = await register_user(db_session, user_data)
    
    assert user.id is not None
    assert user.email == "newuser@test.com"
    assert user.full_name == "New User"
    assert user.is_active is True


@pytest.mark.unit
@pytest.mark.auth
async def test_register_duplicate_user(db_session):
    """Test registrar usuario duplicado debe fallar"""
    from fastapi import HTTPException
    
    user_data = UserCreate(
        email="duplicate@test.com",
        password="pass123"
    )
    
    # Registrar primera vez
    await register_user(db_session, user_data)
    
    # Intentar registrar de nuevo debe fallar
    with pytest.raises(HTTPException) as exc_info:
        await register_user(db_session, user_data)
    
    assert exc_info.value.status_code == 400
    assert "ya está registrado" in exc_info.value.detail