# Data Model

Owner: Daniel Hernandez
Tags: Codebase

Se va a diseñar con estas metas claras:

- 🧱 **Escalable (PostgreSQL vía SQLAlchemy)**
- 🔍 **Auditable y debuggable**
- 💰 **Preparado para billing y límites (Intentions / Créditos)**
- ⚙️ **Aislado del dominio mediante el Patrón Repositorio**

---

# 🗄️ Modelo de Datos – SaaS URL → ePub

Se detalla **entidad por entidad**, explicando:
- qué guarda
- por qué existe
- qué NO guardamos (importante)

---

## 1️⃣ User (core SaaS)

```sql
users
```

```
id              String (PK)
email           String (unique, indexed)
name            String (nullable)
password_hash   String (nullable)   -- null para usuarios OAuth
provider        String              -- "email" | "google"
provider_id     String              -- email | google sub
plan            String              -- "free" (default) | "pro" | "team"
credits         Integer             -- default 5
is_beta_tester  Boolean             -- default true
is_company      Boolean             -- default false
country         String (nullable)
vat_number      String (nullable)
is_verified     Boolean             -- default false
is_active       Boolean             -- default true
created_at      DateTime (timezone)
updated_at      DateTime (timezone, onupdate)
```

### Decisiones importantes

- ✔ Soporte de login nativo (`password_hash`) y OAuth (`provider`/`provider_id`). `password_hash` es nullable porque los usuarios OAuth no tienen password.
- ✔ `credits` incrustado para control rápido del rate limit, recargado a través de intenciones de compra (`PurchaseIntention`).
- ✔ `plan` y `is_beta_tester` para control de límites y features.
- ✔ `is_company` / `country` / `vat_number` para perfil fiscal (facturación futura).
- ✔ Conexiones de nube abstraídas a otra tabla (`cloud_connections`).

---

## 2️⃣ PurchaseIntention (Intención de Compra)

```sql
purchase_intentions
```

```
id              String (PK)
user_id         String (FK → users.id)
tier_requested  String              -- "pro" | "team"
clicked_at      DateTime (timezone, server_default=func.now())
```

📌 **Por qué existe:** Captura cuándo un usuario hace clic en "comprar" un plan. Al crearse, otorga 5 créditos como recompensa. Es un sistema simple de lead generation sin integración con Stripe aún. No tiene campos de `status`, `amount_cents` ni `currency` — es una intención, no una transacción completa.

---

## 3️⃣ CloudConnection (Exportaciones externas)

```sql
cloud_connections
```

```
id              String (PK)
user_id         String (FK, indexed)
provider        String              -- google_drive | dropbox | onedrive
access_token    String
refresh_token   String (nullable)
expires_at      DateTime (nullable)
metadata_info   JSONB (nullable)    -- email, display_name, etc.
created_at      DateTime (timezone)
updated_at      DateTime (timezone, onupdate)
```

👉 Separa las credenciales OAuth externas del modelo de usuario, permitiendo a los usuarios enlazar múltiples cuentas de nubes externas.

---

## 4️⃣ Job (corazón del sistema)

```sql
jobs
```

```
id              String (PK)
user_id         String (FK → users.id)
source_url      String
base_url        String
status          String              -- queued | processing | done | failed
current_step    String (nullable)   -- extracting | normalizing | generating
progress        Integer             -- 0-100
error_code      String (nullable)
error_message   String (nullable)
external_uploads JSON (default {})  -- {"google_drive": {"id":"...","url":"..."}}
created_at      DateTime
started_at      DateTime (nullable)
finished_at     DateTime (nullable)
```

### Claves

- ✔ `error_message` para feedback de UX y debug.
- ✔ `external_uploads` guarda resultados de exportaciones a la nube como dict JSON.
- ✔ `status` usa `queued` (al crear), `processing` (cuando Arq lo toma), `done` (completado) o `failed` (error).
- ❌ No se guardan archivos binarios aquí, usamos la tabla `File` o storage externo (Backblaze).

---

## 5️⃣ JobContent (Artefactos del Pipeline)

```sql
job_contents
```

```
id              String (PK)
job_id          String (FK → jobs.id)
step            String              -- extracted | normalized | metadata | composite_meta | extracted_0 | normalized_1 ...
content_type    String              -- html | text | json
content         Text
created_at      DateTime
```

📌 **Por qué existe:** El pipeline de conversión produce múltiples artefactos intermedios (HTML extraído, HTML normalizado, metadatos JSON). Esta tabla los almacena para depuración, reprocesamiento y generación de EPUBs compuestos. Para jobs compuestos, los steps se numeran (`extracted_0`, `normalized_1`).

---

## 6️⃣ File (output / ePub)

```sql
files
```

```
id              String (PK)
job_id          String (FK → jobs.id)
type            String              -- "epub"
path            String              -- key en B2 (ej. "epubs/{job_id}.epub")
size_bytes      Integer (nullable)
checksum        String (nullable)
is_deleted      Boolean             -- default false
deleted_at      DateTime (nullable)
created_at      DateTime (timezone)
```

📌 `path` contiene la key de Backblaze B2 (S3-compatible). A partir de esta key se generan presigned URLs para descarga. `is_deleted`/`deleted_at` se usan para el retention cleanup automático.

---

# 🔗 Relaciones clave (mental map)

```
User
 ├──CloudConnection (0..N)
 ├──PurchaseIntention (0..N)
 ├──Job (0..N)
 │    ├──JobContent (0..N)
 │    └──File (0..1)
```

---

# 🛡️ Patrón Repositorio (Clean Architecture)

Las rutas de FastAPI (y los Servicios) **no interactúan directamente con SQLAlchemy ni con estos modelos de datos**.

Para cada entidad, existe una clase en `app/domain/repositories/` (e.g. `UserRepository`, `JobRepository`) que expone los métodos CRUD abstractos:
- Ventaja 1: Se oculta el código SQL / SQLAlchemy.
- Ventaja 2: Permite hacer tests mediante `unittest.mock.Mock` sin requerir base de datos de testeo.