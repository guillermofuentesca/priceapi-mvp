"""
Sistema de Autenticación JWT
Maneja registro, login, tokens y password hashing
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from config import settings
from database import get_db, User
from crud import get_user_by_email, create_user

# ========== CONFIGURACIÓN ==========

# Context para hashear passwords
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 scheme para extraer token del header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ========== MODELOS PYDANTIC ==========

class UserCreate(BaseModel):
    """Schema para crear usuario"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None


class UserResponse(BaseModel):
    """Schema para respuesta de usuario (sin password)"""
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema para respuesta de token"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Schema para datos dentro del token"""
    email: Optional[str] = None


# ========== FUNCIONES DE PASSWORD ==========

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que el password coincida con el hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashea un password (trunca a 72 bytes para bcrypt)"""
    # Truncar password a 72 bytes para bcrypt
    password_bytes = password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password_truncated)


# ========== FUNCIONES DE TOKEN JWT ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT
    
    Args:
        data: Datos a incluir en el token (ej: {"sub": "user@email.com"})
        expires_delta: Tiempo de expiración (opcional)
    
    Returns:
        Token JWT como string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    Decodifica un token JWT y extrae el email
    
    Args:
        token: Token JWT
        
    Returns:
        Email del usuario o None si es inválido
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


# ========== AUTENTICACIÓN ==========

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Autentica un usuario verificando email y password
    
    Returns:
        Usuario si las credenciales son válidas, None en caso contrario
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Obtiene el usuario actual desde el token JWT
    
    Esta función se usa como Dependency en endpoints protegidos
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception
    
    user = await get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verifica que el usuario actual esté activo
    
    Raises:
        HTTPException: Si el usuario está desactivado
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user


# ========== REGISTRO DE USUARIO ==========

async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Registra un nuevo usuario
    
    Args:
        db: Sesión de base de datos
        user_data: Datos del usuario a crear
        
    Returns:
        Usuario creado
        
    Raises:
        HTTPException: Si el email ya está registrado
    """
    # Verificar si el usuario ya existe
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Hashear password
    hashed_password = get_password_hash(user_data.password)
    
    # Crear usuario
    user = await create_user(
        db,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        username=user_data.username
    )
    
    await db.commit()
    return user