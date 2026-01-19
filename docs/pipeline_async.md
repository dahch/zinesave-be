# Pipeline async

Tipo: Especificación
Estado: Completado
Fecha de creación: 25 de diciembre de 2025
Última actualización: 25 de diciembre de 2025

# 🔄 Pipeline Async – Diseño Completo (Bootstrap → Escalable)

## 🧠 Idea central

> La API no hace el trabajo pesado.Solo orquesta y delega.
> 

---

## 0️⃣ Estados del Job (base del sistema)

```
queued
processing
extracting
normalizing
generating
exporting
done
failed

```

👉 Aunque al inicio no se muestre todos al cliente, **internamente sí existen**.

---

## 1️⃣ Creación del Job (API Layer)

### POST `/jobs`

**Qué pasa internamente**

1. Se validas:
    - URL
    - Plan
    - Rate limit
2. Creas registro `Job` en DB:
    
    ```json
    {
    "status":"queued",
    "progress":0
    }
    
    ```
    
3. Se devuelve `202 Accepted`
4. Se encola ejecución async

📌 **Nunca procesesar aquí**

---

## 2️⃣ Orquestación async (Bootstrap)

### Opción inicial (sin cola)

```python
bg.add_task(run_pipeline, job_id)

```

✔ Cero coste

❌ Si el server cae, se pierde jobs

👉 Aceptable para early adopters / uso personal.

---

## 3️⃣ run_pipeline(job_id)

Este método **nunca expone lógica HTTP**.

```python
defrun_pipeline(job_id):
    extract(job_id)
    normalize(job_id)
    generate(job_id)
    export(job_id)

```

Pero con **manejo de errores y estado**.

---

## 4️⃣ Paso 1: Extract (Reader Mode)

**Estado:** `extracting`

### Qué hace

- Descarga HTML
- Aplica Reader Mode
- Extrae:
    - Título
    - Autor
    - HTML limpio
    - Texto plano

### Guardas:

- HTML normalizado
- Metadatos

📌 Guardar HTML intermedio **es clave** para debug.

---

## 5️⃣ Paso 2: Normalize (HTML → ePub-ready)

**Estado:** `normalizing`

### Qué hace

- Limpiar etiquetas
- Arreglar:
    - Imágenes
    - Encabezados
    - Links
- Insertar CSS base
- Detectar idioma

📌 Aquí se gana calidad de producto.

---

## 6️⃣ Paso 3: Generate (ePub)

**Estado:** `generating`

### Qué hace

- Generar ePub
- Metadata:
    - title
    - author
    - lang
- Portada básica (opcional)

📦 Output:

- `book.epub`

---

## 7️⃣ Paso 4: Export

**Estado:** `exporting`

### Opciones

- Google Drive
- Local download

📌 El export **no afecta la generación**

Si falla → se puede reintentar solo este paso.

---

## 8️⃣ Finalización

### Success

```json
status ="done"
progress =100

```

### Failure

```json
status ="failed"
error ="EXPORT_FAILED"

```

📌 Job siempre termina en estado final.

---

# 🧱 Separación de responsabilidades (Clean)

```
Application
 ├──JobOrchestrator
 ├──ExtractService
 ├──NormalizeService
 ├──GenerateService
 └──ExportService

```

👉 Cada paso:

- Input claro
- Output claro
- Idempotente (ideal)

---

## 🛡️ Manejo de errores (MUY importante)

| Error | Acción |
| --- | --- |
| URL inválida | fail inmediato |
| Timeout | retry |
| HTML vacío | fail |
| Export falla | retry export |
| ePub corrupto | fail |

📌 Guardar siempre:

- stacktrace
- step
- input

---

## 📊 Progreso (%)

| Paso | Progreso |
| --- | --- |
| queued | 0 |
| extracting | 25 |
| normalizing | 50 |
| generating | 75 |
| exporting | 90 |
| done | 100 |

---

# 🚀 Evolución natural (cuando crezca)

## Versión con cola (misma lógica)

```
API → Queue → Worker

```

Cada paso:

- Puede ser un task
- O pipeline completo

Ejemplo:

```python
@worker.task
defprocess_job(job_id):
    run_pipeline(job_id)

```

📌 **No cambia dominio**, solo infraestructura.

---

# 💡 Decisión clave de bajo coste

👉 **Un pipeline monolítico bien diseñado es mejor que microservicios pobres**