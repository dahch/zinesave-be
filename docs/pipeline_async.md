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
pending
processing
completed
failed
```

👉 Inicialmente el Job se crea como `pending`. A medida que Arq lo toma pasa a `processing`. Si falla, pasa a `failed`.

---

## 1️⃣ Creación del Job (API Layer)

### POST `/jobs`

**Qué pasa internamente (vía `JobService`)**

1. Se validan:
    - URL (SSRF protection).
    - Créditos suficientes del usuario.
    - Prevención de duplicados recientes.
2. Se crea un registro `Job` a través del `JobRepository`:
    ```json
    {
      "status": "pending",
      "progress": 0
    }
    ```
3. Se resta un crédito al usuario.
4. Se encola la ejecución en Redis mediante el `QueueService`:
    ```python
    await self.queue_service.enqueue_job("execute_pipeline", job.id)
    ```
5. Se devuelve el Job al cliente (quien puede hacer polling).

📌 **Las rutas y el servicio nunca procesan HTML aquí**.

---

## 2️⃣ Orquestación async (Redis + Arq Worker)

En el script `app/worker.py` corre de manera independiente el proceso de `Arq`.
La tarea registrada es `execute_pipeline(ctx, job_id)` que llama internamente al `PipelineService`.

✔ Escalabilidad: Puedes levantar N workers conectando al mismo Redis.
✔ Persistencia: Si la API cae, los jobs encolados no se pierden.
✔ Manejo de errores integrados y reintentos (retry) configurables en Arq.

---

## 3️⃣ PipelineService.execute(job_id)

El orquestador en segundo plano (dentro del worker). No conoce HTTP.

```python
async def execute(self, job_id: str):
    self._update_progress(job, 10, "processing")
    
    # 1. Extraction
    content = self.extract_service.extract(url)
    
    # 2. Epub Generation
    epub_bytes = self.epub_service.generate(content)
    
    # 3. Storage
    file_id = self.storage_service.store_b2(epub_bytes)
    self.file_repo.add(File(...))
    
    # 4. Cloud Connections Exports (Drive, Dropbox, OneDrive)
    self._export_to_connected_clouds(...)
```

---

## 4️⃣ Paso 1: Extraction & Normalization

**Servicios involucrados:** `ExtractService`, `NormalizeService`.

### Qué hace

- Descarga HTML (con `httpx` de forma asíncrona).
- Aplica algoritmos tipo Reader Mode (e.g. `readability-lxml`).
- Limpia HTML, sanitiza iframes, scripts y estilos sucios.
- Extrae metadatos (Título, Autor, Length).

---

## 5️⃣ Paso 2: Generate (ePub)

**Servicio involucrado:** `EpubService`.

### Qué hace

- Usa librerías internas (como `ebooklib` o similares) para empaquetar el contenido limpio.
- Adjunta cover básico y tabla de contenidos (TOC).

📦 Output temporal en memoria:
- `Bytes` del EPUB.

---

## 6️⃣ Paso 3: Storage (Backblaze B2)

**Servicio involucrado:** `StorageService`.

El archivo binario no se guarda en PostgreSQL. Se sube a B2 usando `boto3`.

- Se devuelve un path genérico remoto.
- Se crea la entidad `File` a través del `FileRepository`.

---

## 7️⃣ Paso 4: Cloud Exports

**Servicio involucrado:** `CloudService`.

Si el usuario tiene conexiones registradas (`CloudConnectionRepository`):
- Google Drive
- Dropbox
- OneDrive

El `CloudService` toma los bytes del EPUB y los sube a las carpetas configuradas usando los `access_token` correspondientes.

📌 El export **no rompe la conversión**. Si Dropbox falla por token inválido, se loguea (JSON Logger), pero el Job se marca como `completed` porque el archivo en B2 ya existe.

---

## 8️⃣ Finalización

### Success

```json
status = "completed"
progress = 100
```

### Failure

Cualquier excepción grave en el pipeline de `Arq` es atrapada. El job se marca como `failed` guardando el error.

```json
status = "failed"
error_message = "URL_NOT_REACHABLE"
```

---

# 🧱 Separación de responsabilidades (Clean Architecture)

```
app/services/
 ├── PipelineService (Orquesta el Worker)
 ├── JobService (Orquesta la API y encola)
 ├── QueueService (Abstracción sobre Arq/Redis)
 ├── ExtractService (Descarga y limpia)
 ├── EpubService (Generador del binario)
 ├── StorageService (S3 / B2)
 └── CloudService (Drive / Dropbox)
```

👉 Cada paso:
- Tiene inputs/outputs claros.
- Es independiente.
- Tiene tests unitarios.

---

# 💡 Decisión clave de escalabilidad

👉 **Usar Arq sobre Celery:** Arq es nativo en `asyncio`, ligero, rápido y no necesita dependencias inmensas. Perfecto para este flujo basado en I/O.