# 🚀 GUÍA DE SETUP - DÍA 3
## HYBRID90-PRICEAPI-FEB25-V1

Esta guía te llevará paso a paso para configurar todas las integraciones del Día 3.

---

## 📋 PREREQUISITOS

- ✅ Python 3.10+ instalado
- ✅ Git instalado
- ✅ Entorno virtual activado
- ⬜ PostgreSQL instalado
- ⬜ Redis instalado

---

## 1️⃣ INSTALAR POSTGRESQL

### Ubuntu/Debian:
```bash
# Instalar PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Verificar instalación
sudo systemctl status postgresql

# Debe mostrar: active (running)
```

### macOS:
```bash
# Usando Homebrew
brew install postgresql@14
brew services start postgresql@14
```

### Windows:
- Descargar instalador desde: https://www.postgresql.org/download/windows/
- Ejecutar instalador y seguir wizard
- Recordar el password del usuario postgres

---

## 2️⃣ CONFIGURAR BASE DE DATOS

### Crear base de datos y usuario:
```bash
# Acceder a PostgreSQL
sudo -u postgres psql

# Dentro de psql, ejecutar:
CREATE DATABASE pricetracker_db;
CREATE USER pricetracker_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE pricetracker_db TO pricetracker_user;

# Salir
\q
```

### Verificar conexión:
```bash
psql -U pricetracker_user -d pricetracker_db -h localhost
# Te pedirá el password
```

---

## 3️⃣ INSTALAR REDIS

### Ubuntu/Debian:
```bash
# Instalar Redis
sudo apt-get install redis-server

# Iniciar servicio
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verificar que está corriendo
redis-cli ping
# Debe responder: PONG
```

### macOS:
```bash
brew install redis
brew services start redis

# Verificar
redis-cli ping
```

### Windows:
- Descargar Redis desde: https://github.com/microsoftarchive/redis/releases
- O usar Docker:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

---

## 4️⃣ OBTENER RAINFOREST API KEY

1. **Registrarse**: Ve a https://www.rainforestapi.com/
2. **Plan Free**: Selecciona el plan gratuito (1000 requests/mes)
3. **Obtener API Key**: Copia tu API key desde el dashboard
4. **Guardar**: La necesitarás en el paso siguiente

**NOTA**: Si no quieres usar Rainforest API ahora, puedes dejarlo vacío y la aplicación usará datos mock.

---

## 5️⃣ CONFIGURAR VARIABLES DE ENTORNO

```bash
# Copiar el template
cp .env.example .env

# Editar .env con tus valores
nano .env  # o tu editor preferido
```

### Configuración mínima requerida:
```env
DATABASE_URL=postgresql://pricetracker_user:tu_password_seguro@localhost:5432/pricetracker_db
RAINFOREST_API_KEY=tu_api_key_aqui  # Opcional: dejar vacío para modo mock
SECRET_KEY=genera-una-clave-segura-con-openssl-rand-hex-32
```

### Generar SECRET_KEY segura:
```bash
openssl rand -hex 32
```

---

## 6️⃣ INSTALAR DEPENDENCIAS PYTHON

```bash
# Asegurarte que el entorno virtual está activado
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar todas las dependencias
pip install -r requirements.txt

# Verificar instalación
pip list | grep -E "fastapi|sqlalchemy|redis|httpx"
```

---

## 7️⃣ CREAR ESTRUCTURA DE ARCHIVOS

Tu proyecto debe verse así:

```
priceapi-mvp/
├── main.py              # ✅ Archivo principal actualizado
├── config.py            # ✅ Nuevo: Configuración
├── cache.py             # ✅ Nuevo: Redis cache
├── database.py          # ✅ Nuevo: PostgreSQL
├── scraper.py           # ✅ Nuevo: Rainforest API
├── requirements.txt     # ✅ Actualizado
├── .env                 # ✅ Tu configuración (crear desde .env.example)
├── .env.example         # ✅ Template
├── logs/                # ✅ Crear este directorio
│   └── .gitkeep
└── venv/
```

### Crear directorio de logs:
```bash
mkdir -p logs
touch logs/.gitkeep
```

---

## 8️⃣ INICIALIZAR BASE DE DATOS

```bash
# Ejecutar script de inicialización
python -c "
import asyncio
from database import init_db

async def main():
    await init_db()
    print('✅ Base de datos inicializada')

asyncio.run(main())
"
```

O simplemente ejecuta el servidor (creará las tablas automáticamente):

```bash
python main.py
```

---

## 9️⃣ VERIFICAR INSTALACIÓN

### Verificar servicios:
```bash
# PostgreSQL
sudo systemctl status postgresql

# Redis
redis-cli ping
```

### Ejecutar servidor:
```bash
python main.py
```

### Deberías ver:
```
🚀 Iniciando Price Tracker API...
✅ Conexión a Redis establecida exitosamente
✅ Conexión a PostgreSQL exitosa
✅ Tablas de base de datos creadas exitosamente
✅ Price Tracker API v0.2.0 iniciado correctamente
📍 Entorno: development
🌍 Servidor: http://0.0.0.0:8000
📚 Docs: http://0.0.0.0:8000/docs
```

---

## 🔟 PROBAR ENDPOINTS

### 1. Health Check:
```bash
curl http://localhost:8000/health
```

### 2. Obtener precio (modo mock):
```bash
curl "http://localhost:8000/price?asin=B08N5WRWNW&country=US"
```

### 3. Buscar productos:
```bash
curl "http://localhost:8000/search?q=iphone&country=US"
```

### 4. Ver documentación interactiva:
Abre en tu navegador: http://localhost:8000/docs

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [ ] PostgreSQL instalado y corriendo
- [ ] Base de datos `pricetracker_db` creada
- [ ] Usuario `pricetracker_user` creado
- [ ] Redis instalado y corriendo
- [ ] Rainforest API key obtenida (opcional)
- [ ] Archivo `.env` configurado
- [ ] Dependencias instaladas (`pip list`)
- [ ] Directorio `logs/` creado
- [ ] Servidor inicia sin errores
- [ ] `/health` responde correctamente
- [ ] `/docs` es accesible
- [ ] Endpoints funcionan correctamente

---

## 🐛 TROUBLESHOOTING

### Error: "cannot connect to PostgreSQL"
```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql
sudo systemctl start postgresql

# Verificar credenciales en .env
# DATABASE_URL debe coincidir con tu configuración
```

### Error: "cannot connect to Redis"
```bash
# Verificar Redis
redis-cli ping

# Si no responde PONG:
sudo systemctl start redis-server
```

### Error: "ModuleNotFoundError"
```bash
# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

### Error: "Permission denied" en logs/
```bash
# Dar permisos al directorio
chmod 755 logs/
```

### La API usa datos mock en vez de Rainforest
- Esto es normal si no has configurado `RAINFOREST_API_KEY`
- Verifica en logs: "Retornando datos MOCK"
- Para usar API real, configura la key en `.env`

---

## 📚 SIGUIENTES PASOS

Una vez que todo esté funcionando:

1. **Día 4**: Implementar sistema de autenticación JWT
2. **Día 5**: Setup de testing con pytest
3. **Día 6**: Deploy a Railway

---

## 🆘 AYUDA

Si tienes problemas:

1. Revisa los logs en `logs/app.log`
2. Verifica que todos los servicios estén corriendo
3. Confirma que `.env` está correctamente configurado
4. Revisa la salida de `python main.py` para ver mensajes de error

---

**¡ÉXITO!** 🎉

Si llegaste hasta aquí y todo funciona, has completado exitosamente el Día 3.
Tu API ahora tiene:
- ✅ Integración con Rainforest API
- ✅ Sistema de caché con Redis
- ✅ Persistencia con PostgreSQL
- ✅ Manejo robusto de errores
- ✅ Logging completo
