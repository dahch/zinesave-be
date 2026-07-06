# Pipeline async

Tipo: Especificación
Estado: Completado
Fecha de creación: 25 de diciembre de 2025
Última actualización: 16 de junio de 2026

# 🔄 Pipeline Async – Diseño Completo (Escalable vía Arq+Redis)

## 🧠 Idea central

> La API no hace el trabajo pesado. Solo orquesta y delega. El motor de fondo (`Arq`) se encarga del procesamiento usando una cola persistente (`Redis`).
> 

---

## 0️⃣ Estados del Job (base del sistema)

```
queued
processing
done
failed
```

👉 Inicialmente el Job se crea como `queued`. A medida que Arq lo toma pasa a `processing`. Si se completa con éxito, pasa a `done`. Si falla, pasa a `failed`.

---

## 1️⃣ Creación del Job (API Layer)

### POST `/jobs` (simple)

**Qué pasa internamente (vía `JobService`)**

1. Se validan:
    - URL (SSRF protection: bloquea IPs privadas, localhost, metadata endpoints).
    - Créditos suficientes del usuario (mínimo 1).
    - Prevención de duplicados recientes (misma URL en últimos 10 minutos).
2. Se crea un registro `Job` a través del `JobRepository`:
    ```json
    {
      "status": "queued",
      "progress": 0
    }
    ```
3. Se resta un crédito al usuario.
4. Se encola la ejecución en Redis mediante el `QueueService`:
    ```python
    await self.queue_service.enqueue_job("execute_pipeline", job.id)
    ```
5. Se devuelve el Job al cliente (quien puede hacer polling).

### POST `/jobs/composite` (múltiples URLs)

Variante que acepta un array de URLs más un título. Almacena los metadatos como `JobContent` con step `composite_meta` (JSON con `urls` y `title`). El pipeline detecta `base_url == "composite"` y ejecuta el flujo compuesto.

📌 **Las rutas y el servicio nunca procesan HTML aquí**.

---

## 2️⃣ Orquestación async (Redis + Arq Worker)

En el script `app/worker.py` corre de manera independiente el proceso de `Arq`.
La tarea registrada es `execute_pipeline(ctx, job_id)` que llama internamente al `PipelineService`.

✔ Escalabilidad: Puedes levantar N workers conectando al mismo Redis.
✔ Persistencia: Si la API cae, los jobs encolados no se pierden.
✔ Manejo de errores integrados y reintentos (retry) configurables en Arq.

---

## 3️⃣ PipelineService (run_pipeline)

El orquestador en segundo plano (dentro del worker). Es una función síncrona que se ejecuta en un thread separado para no bloquear el event loop de Arq. No conoce HTTP.

```python
def run_pipeline(job_id: str, db_factory):
    db = db_factory()
    job = db.query(Job).filter(Job.id == job_id).first()
    job.status = "processing"
    db.commit()

    if job.base_url == "composite":
        run_composite_pipeline(job, db)  # Multi-URL
    else:
        extract_content(db, job)         # Step 1
        normalize_html(db, job)          # Step 2
        generate_epub(db, job)           # Step 3

    # Step 4: Cloud upload is NOW MANUAL via POST /jobs/{id}/upload

    job.status = "done"
    job.progress = 100
    db.commit()
```

---

## 4️⃣ Paso 1: Extraction

**Servicios involucrados:** `extract_content` / `fetch_and_extract` (funciones en `app/services/extract_service.py`).

### Qué hace

- Descarga HTML (con `requests` de forma síncrona).
- Preprocesa HTML para rescatar imágenes (Substack/Medium específico: `div.captioned-image-container` → `p > img`).
- Aplica algoritmos tipo Reader Mode vía `readability-lxml`.
- Extrae metadatos (Título, Autor, URL) mediante `extract_metadata`.
- Guarda el contenido extraído como `JobContent` (step `extracted`, type `html`).
- Guarda los metadatos como `JobContent` (step `metadata`, type `json`).

## 5️⃣ Paso 1.5: Normalization

**Servicios involucrados:** `normalize_html` / `process_html_normalization` (funciones en `app/services/normalize_service.py`)

### Qué hace

- Elimina etiquetas no deseadas (`script`, `style`, `iframe`, `noscript`).
- Normaliza headings (solo un `h1`, el resto → `h2`).
- Limpia atributos (solo conserva `href`, `src`, `alt`).
- Inyecta CSS base para una tipografía limpia (serif, line-height).
- Detecta idioma con `langdetect` y cuenta palabras.
- Guarda el contenido normalizado como `JobContent` (step `normalized`, type `html`).

---

## 6️⃣ Paso 2: Generate (ePub)

**Servicio involucrado:** `generate_epub` en `app/services/epub_service.py`.

### Qué hace

- Usa `ebooklib` para empaquetar el contenido limpio.
- Genera cover visual (fondo oscuro con título, dominio y fecha) usando `Pillow`.
- Procesa imágenes (descarga y embebe imágenes locales/remotas) vía `image_service`.
- Adjunta tabla de contenidos (TOC) y navegación.

📦 Output: Se escribe a un archivo temporal, se sube a Backblaze B2 y se registra como entidad `File` en la BD.

---

## 7️⃣ Paso 3: Storage (Backblaze B2)

**Servicio involucrado:** `StorageService` (singleton en `app/services/storage_service.py`).

El archivo binario no se guarda en PostgreSQL. Se sube a B2 usando `boto3` con API S3-compatible.

- Key en B2: `epubs/{job_id}.epub`
- Se crea la entidad `File` a través del `FileRepository`.
- Descarga vía presigned URLs (expiración: 1 hora).

---

## 8️⃣ (Manual) Cloud Upload

**Servicio involucrado:** `UploadService` y `CloudService`.

La exportación a la nube **ya no es automática**. El usuario debe llamar explícitamente a `POST /jobs/{job_id}/upload` con el provider deseado (`google_drive`, `dropbox`, `onedrive` o `all`).

El `UploadService`:
1. Verifica que el job pertenece al usuario y tiene un EPUB listo.
2. Descarga el archivo de B2 a un directorio temporal.
3. Para cada provider solicitado, obtiene la conexión OAuth y sube el archivo.
4. Actualiza `job.external_uploads` con los resultados.
5. Retorna objetos `success` y `errors`.

📌 El upload **no rompe la conversión**. Si un provider falla, los demás continúan y se reportan errores por separado.

---

## 9️⃣ Finalización

### Success

```json
status = "done"
progress = 100
```

### Failure

Cualquier excepción grave en el pipeline de `Arq` es atrapada. El job se marca como `failed` guardando el error.

```json
status = "failed"
error_message = "URL_NOT_REACHABLE"
```

### Pipeline Compuesto

Para jobs con `base_url == "composite"`, el flujo es diferente:
1. Se lee el `JobContent` con step `composite_meta` (contiene `urls` y `title`).
2. Para cada URL, se ejecutan extracción y normalización de forma secuencial.
3. Los steps se numeran (`extracted_0`, `normalized_1`, etc.).
4. Se combinan metadatos (título, autores concatenados).
5. Se genera un EPUB único con todos los capítulos.

---

# 🧱 Separación de responsabilidades (Clean Architecture)

```
app/services/
 ├── pipeline_service.py   (Orquesta el Worker, funciones run_pipeline / run_composite_pipeline)
 ├── job_service.py        (Orquesta la API y encola)
 ├── queue_service.py      (Abstracción sobre Arq/Redis)
 ├── extract_service.py    (Descarga HTML, reader mode, rescate de imágenes)
 ├── normalize_service.py  (Limpieza HTML, normalización, detección de idioma)
 ├── epub_service.py       (Generador del binario EPUB vía ebooklib)
 ├── cover_service.py      (Generación de portada vía Pillow)
 ├── image_service.py      (Descarga y embebido de imágenes)
 ├── storage_service.py    (S3 / B2 upload, download, presigned URLs, delete)
 ├── cloud_service.py      (Abstracción para Drive / Dropbox / OneDrive)
 ├── upload_service.py     (Upload manual a cloud providers)
 ├── retention_service.py  (Cron: limpieza de archivos expirados de users free)
 └── email_service.py      (Envío de emails vía MailerSend)
```

👉 Cada paso:
- Tiene inputs/outputs claros.
- Es independiente.
- Tiene tests unitarios.

---

# 💡 Decisión clave de escalabilidad

👉 **Usar Arq sobre Celery:** Arq es nativo en `asyncio`, ligero, rápido y no necesita dependencias inmensas. Perfecto para este flujo basado en I/O. El worker usa `poll_delay=30` para minimizar comandos en Upstash Redis (free tier).