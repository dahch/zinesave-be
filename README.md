# Reader to EPUB Converter

## Descripción
Este proyecto es una API construida con FastAPI diseñada para convertir contenido de lectura (artículos, etc.) a formato EPUB. Permite a los usuarios gestionar trabajos de conversión, realizar seguimiento del uso mediante créditos y exportar automáticamente a sus servicios de almacenamiento en la nube.

Está construido siguiendo los principios de **Clean Architecture** y el patrón **Repositorio**, asegurando escalabilidad, facilidad de mantenimiento y un acoplamiento nulo entre los servicios de negocio y la capa de base de datos.

## Funcionalidades Principales
- **Conversión**: Transforma URLs y contenido a archivos EPUB con limpieza de código (Reader Mode).
- **Cola de Tareas (Async Worker)**: Utiliza `Arq` y Redis para el procesamiento pesado en segundo plano sin bloquear la API.
- **Almacenamiento (B2)**: Integración con Backblaze B2 para el almacenamiento genérico de archivos generados.
- **Exportación en la Nube**: Integraciones nativas (OAuth) para exportar directamente a Google Drive, Dropbox y OneDrive.
- **Sistema de Créditos**: Sistema basado en *Intentions* para la recarga y cobro de conversiones.
- **Autenticación Completa**: Login propio con JWT (Argon2) y OAuth (Google).

## Endpoints Principales

- **Auth (`/auth`)**: Login clásico, registro, confirmación de correo y Google OAuth.
- **Usuario (`/me`)**: Obtención y actualización del perfil del usuario logueado.
- **Intentions (`/me/intentions`)**: Gestión de recarga de créditos y compras.
- **Trabajos (`/jobs`)**: Creación asíncrona, listado y gestión de trabajos de conversión.
- **Upload (`/upload`)**: Descarga o almacenamiento directo de archivos convertidos.

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

**Base de Datos y Cola:**
- `DATABASE_URL`: URL de conexión a PostgreSQL.
- `REDIS_URL`: URL de conexión a Redis (ej. `redis://localhost:6379`).

**Seguridad:**
- `JWT_SECRET`: Llave secreta para firmar tokens JWT.

**Almacenamiento y Nube:**
- `B2_BUCKET_NAME`, `B2_ENDPOINT_URL`, `B2_KEY_ID`, `B2_APPLICATION_KEY`: Credenciales de Backblaze B2.
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: Credenciales de Google OAuth.
- `DROPBOX_CLIENT_ID` / `DROPBOX_CLIENT_SECRET`: Integración con Dropbox.
- `ONEDRIVE_CLIENT_ID` / `ONEDRIVE_CLIENT_SECRET`: Integración con OneDrive.

**Monitoreo (Opcional):**
- `SENTRY_DSN`: DSN de Sentry para reporte de errores.

### 3. Ejecutar Infraestructura Base
La aplicación requiere Redis y Postgres. Puedes levantar dependencias externas vía Docker:

```bash
docker-compose up -d redis
```

### 4. Ejecutar el Worker (Arq)
El worker es el proceso encargado de ejecutar las conversiones en segundo plano.

**Opción A: Ejecución Local (Recomendado para Dev)**
Si prefieres correrlo en tu máquina junto con tus cambios en vivo:
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

### 6. Ejecutar las Pruebas Unitarias (TDD)
El proyecto contiene una suite extensiva de pruebas mediante `pytest` basada en Mocks sobre el patrón Repositorio.

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Arquitectura y Documentación Adicional
Todo el detalle del diseño del modelo de datos (`data_model.md`), la justificación del flujo asíncrono (`pipeline_async.md`) y las instrucciones para interactuar o programar con Inteligencia Artificial se encuentran en la carpeta `docs/` y en la raíz bajo `AI_CONTEXT.md`.
