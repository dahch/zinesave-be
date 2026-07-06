# ZineSave — Reader to EPUB Converter
> API for converting web articles to EPUB format with cloud storage integration.

## Descripción
ZineSave es una API construida con FastAPI que convierte contenido web (artículos, URLs) a formato EPUB. Los usuarios pueden gestionar trabajos de conversión, realizar seguimiento del uso mediante créditos, y exportar manualmente a servicios de almacenamiento en la nube (Google Drive, Dropbox, OneDrive). El proyecto está pensado como SaaS con sistema de planes, intenciones de compra y autenticación OAuth.

Está construido siguiendo los principios de **Clean Architecture** y el patrón **Repositorio**, asegurando escalabilidad, facilidad de mantenimiento y un acoplamiento nulo entre los servicios de negocio y la capa de base de datos.

## Funcionalidades Principales
- **Conversión**: Transforma URLs a archivos EPUB con limpieza de código (Reader Mode vía `readability-lxml`).
- **EPUBs Compuestos**: Convierte múltiples URLs en un solo EPUB (límite por plan: 4 free, 10 pro).
- **Cola de Tareas (Async Worker)**: Utiliza `Arq` + Redis para el procesamiento pesado en segundo plano sin bloquear la API.
- **Almacenamiento (B2)**: Integración con Backblaze B2 para almacenar EPUBS generados; descarga vía presigned URLs.
- **Exportación Manual a la Nube**: Integraciones nativas OAuth para exportar a Google Drive, Dropbox y OneDrive (`POST /jobs/{id}/upload`).
- **Sistema de Créditos**: Créditos consumidos por cada conversión; se recargan al capturar una intención de compra.
- **Autenticación Completa**: Login propio con JWT (Argon2), verificación de email y OAuth (Google, Dropbox, OneDrive).
- **Dashboard**: Endpoint `/me/dashboard` con resumen de uso, jobs recientes y conexiones activas.
- **Retención Automática**: Los archivos de usuarios free se eliminan tras 7 días (cron job en Arq).

## Endpoints Principales

- **Auth (`/auth`)**: Login, registro, verificación de email, forgot/reset password, OAuth (Google, Dropbox, OneDrive).
- **Usuario (`/me`)**: Perfil, actualización (company/country/VAT), uso, dashboard.
- **Intentions (`/intentions`)**: Captura de intención de compra de plan (otorga 5 créditos).
- **Trabajos (`/jobs`)**: Creación asíncrona, listado paginado, estado, descarga (presigned URL), creación compuesta.
- **Upload a la Nube (`POST /jobs/{id}/upload`)**: Sube manualmente un EPUB completado a servicios cloud conectados.

## Configuración y Puesta en Marcha

### Prerrequisitos
- Python 3.11+
- PostgreSQL
- Redis
- Docker y Docker Compose (para entornos de base de datos y Worker aislados)

### 1. Configuración del Entorno Virtual
Crea y activa un entorno virtual para aislar las dependencias:

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno (Mac/Linux)
source .venv/bin/activate

# Activar entorno (Windows)
# .venv\Scripts\activate
```

Instala las dependencias necesarias:
```bash
pip install -r requirements.txt
```

### 2. Variables de Entorno (.env)
Crea un archivo `.env` en la raíz del proyecto. Este archivo es **requerido** para que la aplicación funcione y es interpretado nativamente mediante `pydantic-settings` en `app/core/config.py`.

**Generales:**
- `FRONTEND_URL` (requerido): URL del frontend (ej. `http://localhost:3000`).
- `BACKEND_URL` (requerido): URL del backend (ej. `http://localhost:8000`).
- `ENVIRONMENT`: `production` o `development` (default: `production`; en desarrollo desbloquea rutas debug como `/sentry-debug`).

**Base de Datos y Cola:**
- `DATABASE_URL`: URL de conexión a PostgreSQL (ej. `postgresql://user:pass@localhost:5432/zinesave`).
- `REDIS_URL`: URL de conexión a Redis (ej. `redis://localhost:6379`).
- `REDIS_HOST`: Host de Redis (default: `redis`, usado cuando no se provee `REDIS_URL`).
- `REDIS_PORT`: Puerto de Redis (default: `6379`).

**Seguridad:**
- `JWT_SECRET`: Llave secreta para firmar tokens JWT.

**Almacenamiento (Backblaze B2):**
- `B2_BUCKET_NAME`, `B2_ENDPOINT_URL`, `B2_KEY_ID`, `B2_APPLICATION_KEY`: Credenciales de Backblaze B2.

**Google OAuth:**
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_PROJECT_ID`: Credenciales de Google OAuth.

**Dropbox OAuth:**
- `DROPBOX_CLIENT_ID` / `DROPBOX_CLIENT_SECRET`: Integración con Dropbox.

**OneDrive OAuth:**
- `ONEDRIVE_CLIENT_ID` / `ONEDRIVE_CLIENT_SECRET`: Integración con OneDrive.
- `ONEDRIVE_TENANT_ID` / `ONEDRIVE_CLIENT_SECRET_ID`: Opcionales para configuración avanzada de OneDrive.

**Email (MailerSend):**
- `MAILERSEND_API_KEY`: API key de MailerSend para envío de emails.
- `MAILERSEND_FROM_EMAIL`: Dirección from para correos (default: `noreply@zinesave.io`).
- `CONTACT_EMAIL`: Dirección de contacto para el footer de emails (default: `support@zinesave.io`).

**Monitoreo (Opcional):**
- `SENTRY_DSN`: DSN de Sentry para reporte de errores.

### 3. Ejecutar Infraestructura Base
La aplicación requiere Redis y PostgreSQL. Puedes levantar dependencias externas vía Docker:

```bash
docker-compose up -d redis
```

También necesitas una instancia de PostgreSQL accesible (local o vía servicio como NeonDB).

### 4. Ejecutar el Worker (Arq)
El worker es el proceso encargado de ejecutar las conversiones en segundo plano.

**Opción A: Ejecución Local (Recomendado para Dev)**
```bash
source .venv/bin/activate
arq app.worker.WorkerSettings
```

**Opción B: Docker**
```bash
docker-compose up -d --build worker
```

### 5. Ejecutar la API
Levanta el servidor de desarrollo de FastAPI:

```bash
uvicorn app.main:app --reload
```
La API estará disponible en `http://localhost:8000`.
La documentación Swagger se puede ver en `http://localhost:8000/docs`.

### 6. Ejecutar las Pruebas Unitarias
El proyecto contiene una suite extensiva de pruebas mediante `pytest` con un mínimo de cobertura del 70%.

```bash
source .venv/bin/activate
pytest tests/ -v --cov=app --cov-fail-under=70
```

### 7. Despliegue (CI/CD)

El proyecto se despliega en **Fly.io**. El pipeline CI/CD (`.github/workflows/ci.yml`) ejecuta:
1. Linting con Ruff
2. Tests con pytest (cobertura mínima 70%)
3. Deploy a Fly.io automático al hacer push a `main`

Para deploy manual:
```bash
flyctl deploy
```

## Arquitectura y Documentación Adicional
Todo el detalle del diseño del modelo de datos (`docs/data_model.md`), el contrato de API (`docs/api_contract.md`), la justificación del flujo asíncrono (`docs/pipeline_async.md`) y el diseño arquitectónico (`docs/architecture.md`) se encuentran en la carpeta `docs/`. Las instrucciones para IA están en `AI_CONTEXT.md` en la raíz.
