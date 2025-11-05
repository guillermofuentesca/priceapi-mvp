# 🚀 HYBRID90-PRICEAPI-FEB25-V1

**API REST de Comparación de Precios en Tiempo Real**

Una API robusta para rastrear, comparar y monitorear precios de productos de Amazon en múltiples países.

---

## 📊 ESTADO DEL PROYECTO

### ✅ Completado
- **Día 1-2**: Setup inicial + API Mock con FastAPI
- **Día 3**: Integración Rainforest API + Redis + PostgreSQL

### 🚧 En Progreso
- **Día 4**: Base de datos completa + Migraciones
- **Día 5**: Sistema de autenticación JWT

### 📅 Roadmap
- **Semana 1**: Fundamentos (API, BD, Auth, Tests, Deploy)
- **Semana 2**: Features avanzadas (Alertas, WebSockets, Rate Limiting)
- **Semana 3**: Frontend React/Next.js
- **Semana 4+**: Features premium y escalabilidad

---

## 🎯 CARACTERÍSTICAS ACTUALES

### Core API (Día 3)
- ✅ Scraping de precios de Amazon (Rainforest API)
- ✅ Sistema de caché con Redis (TTL configurable)
- ✅ Persistencia en PostgreSQL
- ✅ Historial de precios
- ✅ Búsqueda de productos
- ✅ Tracking de productos
- ✅ Health checks
- ✅ Documentación interactiva (Swagger)
- ✅ Logging robusto
- ✅ Manejo de errores y rate limiting

### Soporte Multi-país
- 🇺🇸 Estados Unidos (US)
- 🇲🇽 México (MX)
- 🇨🇦 Canadá (CA)
- 🇬🇧 Reino Unido (UK)
- 🇩🇪 Alemania (DE)
- 🇫🇷 Francia (FR)
- 🇮🇹 Italia (IT)
- 🇪🇸 España (ES)
- 🇯🇵 Japón (JP)
- 🇮🇳 India (IN)
- 🇧🇷 Brasil (BR)

---

## 🛠️ TECH STACK

### Backend
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.10+
- **Database**: PostgreSQL 14+ (con SQLAlchemy async)
- **Cache**: Redis 6+
- **Scraping**: Rainforest API
- **Server**: Uvicorn (ASGI)

### DevOps
- **Testing**: pytest + pytest-asyncio
- **CI/CD**: GitHub Actions (próximamente)
- **Deploy**: Railway (próximamente)
- **Monitoring**: Logs estructurados

---

## 📦 INSTALACIÓN RÁPIDA

### Prerequisitos
```bash
# Verificar versiones
python --version  # 3.10+
psql --version    # PostgreSQL 14+
redis-cli --version  # Redis 6+
```

### Setup (5 minutos)
```bash
# 1. Clonar repositorio
git clone <tu-repo>
cd priceapi-mvp

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus valores

# 5. Iniciar servicios externos
sudo systemctl start postgresql
sudo systemctl start redis-server

# 6. Crear base de datos
sudo -u postgres psql
CREATE DATABASE pricetracker_db;
CREATE USER pricetracker_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE pricetracker_db TO pricetracker_user;
\q

# 7. Iniciar servidor
python main.py
```

📚 **Para guía detallada**: Ver [SETUP_DIA3.md](./SETUP_DIA3.md)

---

## 🚀 USO RÁPIDO

### Iniciar servidor
```bash
python main.py
# o
uvicorn main:app --reload
```

### Documentación interactiva
```
http://localhost:8000/docs
```

### Ejemplos de uso

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. Obtener precio de producto
```bash
curl "http://localhost:8000/price?asin=B08N5WRWNW&country=US"
```

#### 3. Buscar productos
```bash
curl "http://localhost:8000/search?q=iphone&country=US"
```

#### 4. Ver historial de precios
```bash
curl "http://localhost:8000/history/B08N5WRWNW?country=US"
```

#### 5. Trackear producto
```bash
curl -X POST "http://localhost:8000/track" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "B08N5WRWNW",
    "country": "US",
    "alert_price": 899.99
  }'
```

---

## 📁 ESTRUCTURA DEL PROYECTO

```
priceapi-mvp/
├── main.py              # Aplicación principal FastAPI
├── config.py            # Configuración y variables de entorno
├── cache.py             # Sistema de caché Redis
├── database.py          # Modelos y conexión PostgreSQL
├── scraper.py           # Cliente Rainforest API
├── requirements.txt     # Dependencias Python
├── .env                 # Variables de entorno (no subir a Git)
├── .env.example         # Template de configuración
├── SETUP_DIA3.md        # Guía de instalación detallada
├── logs/                # Logs de la aplicación
│   └── app.log
└── venv/                # Entorno virtual Python
```

---

## 🔑 VARIABLES DE ENTORNO PRINCIPALES

```env
# Base de datos
DATABASE_URL=postgresql://user:pass@localhost:5432/pricetracker_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Rainforest API
RAINFOREST_API_KEY=tu_api_key_aqui  # Opcional para desarrollo

# Seguridad
SECRET_KEY=genera-con-openssl-rand-hex-32
```

Ver `.env.example` para configuración completa.

---

## 📊 ENDPOINTS DISPONIBLES

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/health` | Health check |
| GET | `/docs` | Documentación Swagger |
| GET | `/price` | Obtener precio actual |
| GET | `/product/{asin}` | Detalle de producto |
| GET | `/search` | Buscar productos |
| GET | `/history/{asin}` | Historial de precios |
| POST | `/track` | Trackear producto |
| GET | `/admin/stats` | Estadísticas |
| GET | `/admin/cache/clear` | Limpiar caché |

---

## 🧪 TESTING

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio pytest-cov

# Ejecutar tests (próximamente - Día 6)
pytest

# Con coverage
pytest --cov=. --cov-report=html
```

---

## 🚢 DEPLOYMENT

### Railway (Recomendado)
```bash
# Próximamente - Día 7
# 1. Crear cuenta en Railway
# 2. Conectar repositorio
# 3. Configurar variables de entorno
# 4. Deploy automático con git push
```

---

## 📈 ROADMAP DETALLADO

### Semana 1: Fundamentos (Días 1-7)
- [x] Día 1-2: Setup + API Mock
- [x] Día 3: Integraciones (Rainforest + Redis + PostgreSQL)
- [ ] Día 4: Base de datos completa + Migraciones (Alembic)
- [ ] Día 5: Autenticación JWT
- [ ] Día 6: Testing (pytest + coverage)
- [ ] Día 7: Deploy Railway v1

### Semana 2: Features Avanzadas (Días 8-14)
- [ ] Día 8-9: Sistema de alertas por email
- [ ] Día 10-11: WebSockets para updates en tiempo real
- [ ] Día 12-13: Rate limiting avanzado + Optimización
- [ ] Día 14: Documentación técnica completa

### Semana 3: Frontend (Días 15-21)
- [ ] Día 15-16: Setup Next.js + TailwindCSS
- [ ] Día 17-18: Páginas principales (Dashboard, Search, Detail)
- [ ] Día 19-20: Estado global + Forms
- [ ] Día 21: Deploy frontend (Vercel)

### Semana 4+: Escalabilidad (Días 22-45)
- [ ] Comparador multi-tienda
- [ ] Analytics dashboard
- [ ] Admin panel
- [ ] Testing E2E
- [ ] Monitoring (Sentry)
- [ ] Launch preparation

---

## 🤝 CONTRIBUIR

Este es un proyecto en desarrollo activo. Contributions son bienvenidas:

1. Fork el repositorio
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 LICENCIA

MIT License - Ver archivo LICENSE para más detalles

---

## 📧 CONTACTO

**Proyecto**: HYBRID90-PRICEAPI-FEB25-V1
**Versión Actual**: 0.2.0 (Día 3)
**Status**: En Desarrollo Activo 🚧

---

## 🙏 AGRADECIMIENTOS

- **FastAPI**: Framework increíble para APIs modernas
- **Rainforest API**: Scraping de Amazon simplificado
- **Railway**: Hosting gratuito para PostgreSQL
- **Redis**: Caché ultra-rápido

---

## 📚 DOCUMENTACIÓN ADICIONAL

- [Guía de Setup Detallada](./SETUP_DIA3.md)
- [Configuración de Variables](./.env.example)
- [API Docs](http://localhost:8000/docs) (cuando el servidor esté corriendo)

---

**⭐ Si este proyecto te es útil, dale una estrella!**

**🚀 Happy Coding!**
