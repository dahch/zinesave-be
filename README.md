# Reader to EPUB Converter

## Descripción
Este proyecto es una API construida con FastAPI diseñada para convertir contenido de lectura (artículos, etc.) a formato EPUB. Permite a los usuarios gestionar trabajos de conversión, subir archivos e integrarse con servicios de almacenamiento en la nube.

## Funcionalidades Principales
- **Conversión**: Transforma URLs y contenido a archivos EPUB.
- **Cola de Tareas**: Utiliza `arq` y Redis para procesamiento asíncrono en segundo plano.
- **Almacenamiento**: Integración con Backblaze B2 para almacenamiento de archivos generados.
- **Autenticación**: Soporte para autenticación vía Google OAuth y gestión de usuarios.

## Endpoints Principales

### Auth (`/auth`)
- Gestión de autenticación y login con Google.

### Usuario (`/me`)
- Obtención de información del usuario actual.

### Trabajos (`/jobs`)
- Creación, listado y gestión de trabajos de conversión.

### Upload (`/upload`)
- Subida directa de archivos para procesar.

### Otros
- `GET /`: Healthcheck de la API.
- `GET /sentry-debug`: Endpoint de prueba para Sentry.

## Configuración y Puesta en Marcha

### Prerrequisitos
- Python 3.11+
- Docker y Docker Compose (para Redis y Worker)

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
Crea un archivo `.env` en la raíz del proyecto. Este archivo es **requerido** para que la aplicación funcione. Debe contener las siguientes variables:

**Base de Datos y Cola:**
- `DATABASE_URL`: URL de conexión a PostgreSQL (ej. `postgresql+psycopg2://user:pass@host/db`).
- `REDIS_URL`: URL de conexión a Redis (ej. `redis://localhost:6379`).

**Seguridad:**
- `JWT_SECRET`: Llave secreta para firmar tokens JWT.

**Almacenamiento (Backblaze B2):**
- `B2_BUCKET_NAME`: Nombre del bucket.
- `B2_ENDPOINT_URL`: Endpoint de B2.
- `B2_KEY_ID`: Key ID de B2.
- `B2_APPLICATION_KEY`: Application Key de B2.

**Integraciones y Auth:**
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: Credenciales de Google OAuth.
- `DROPBOX_CLIENT_ID` / `DROPBOX_CLIENT_SECRET`: (Opcional) Para integración con Dropbox.
- `ONEDRIVE_CLIENT_ID` / `ONEDRIVE_CLIENT_SECRET`: (Opcional) Para integración con OneDrive.

**Monitoreo:**
- `SENTRY_DSN`: (Opcional) DSN de Sentry para reporte de errores.

### 3. Ejecutar Redis
La aplicación requiere Redis para la cola de tareas. Puedes levantarlo usando Docker Compose (definido en `docker-compose.yml`):

```bash
docker-compose up -d redis
```

### 4. Ejecutar el Worker
El worker es el proceso encargado de ejecutar las conversiones en segundo plano.

**Opción A: Docker (Recomendada)**
Esto construirá la imagen usando el `Dockerfile` y levantará el contenedor del worker:

```bash
docker-compose up -d --build worker
```
O manualmente:
```bash
docker build -t reader-worker .
docker run --env-file .env reader-worker
```

**Opción B: Ejecución Local**
Si prefieres correrlo en tu máquina (asegúrate de que Redis esté corriendo):
```bash
arq app.worker.WorkerSettings
```

### 5. Ejecutar la API
Levanta el servidor de desarrollo de FastAPI:

```bash
uvicorn app.main:app --reload
```
La API estará disponible en `http://localhost:8000`.
La documentación interactiva se puede ver en `http://localhost:8000/docs`.
