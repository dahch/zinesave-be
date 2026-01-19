# Data Model

Owner: Daniel Hernandez
Tags: Codebase

Se va a diseñar con estas metas claras:

- 🧱 **Simple hoy (SQLite)**
- 🔁 **Migrable mañana (PostgreSQL)**
- 🔍 **Auditable y debuggable**
- 💰 **Preparado para billing y límites**
- ⚙️ **Alineado con el pipeline async que ya definimos**

---

# 🗄️ Modelo de Datos – SaaS URL → ePub

Se detalla **entidad por entidad**, explicando:

- qué guarda
- por qué existe
- qué NO guardamos (importante)

---

## 1️⃣ User (core SaaS)

```sql
users

```

```
id              UUID (PK)
email           TEXT (unique, indexed)
name            TEXT
provider        TEXT        -- google
provider_id     TEXT        -- google sub
plan            TEXT        -- free | pro | team
is_active       BOOLEAN
created_at      TIMESTAMP
updated_at      TIMESTAMP

```

### Decisiones importantes

- ❌ No passwords (OAuth only)
- ✔ Plan en la tabla (rápido para límites)
- ✔ Provider desacoplado (futuro GitHub)

---

## 2️⃣ Usage (billing técnico)

```sql
usage

```

```
id              UUID (PK)
user_id         UUID (FK)
period          TEXT        -- 2025-01
jobs_used       INTEGER
jobs_limit      INTEGER
reset_at        TIMESTAMP

```

📌 **Separar usage de user** nos salva cuando agreguemos Stripe.

---

## 3️⃣ Job (corazón del sistema)

```sql
jobs

```

```
id              UUID (PK)
user_id         UUID (FK)
source_url      TEXT
status          TEXT        -- queued | processing | done | failed
current_step    TEXT        -- extracting | generating...
progress        INTEGER     -- 0-100
error_code      TEXT
error_message   TEXT

created_at      TIMESTAMP
started_at      TIMESTAMP
finished_at     TIMESTAMP

```

### Claves

- ✔ `current_step` = debug fácil
- ✔ `error_code` = UX limpia
- ❌ No guardar archivos aquí

---

## 4️⃣ Article (contenido lógico)

```sql
articles

```

```
id              UUID (PK)
job_id          UUID (FK)
title           TEXT
author          TEXT
language        TEXT
word_count      INTEGER
source_url      TEXT

created_at      TIMESTAMP

```

📌 Esto te permite:

- Historial
- Re-generar
- Multi-capítulo después

---

## 5️⃣ JobContent (intermedios 🔥)

```sql
job_contents

```

```
id              UUID (PK)
job_id          UUID (FK)
step            TEXT        -- extracted | normalized
content_type    TEXT        -- html | text
content         TEXT        -- HTML limpio
created_at      TIMESTAMP

```

👉 **Tabla clave para debugging**

- Podemos reintentar sin volver a descargar
- Posibilita inspeccionar errores de Readability

---

## 6️⃣ File (outputs)

```sql
files

```

```
id              UUID (PK)
job_id          UUID (FK)
type            TEXT        -- epub
path            TEXT        -- local or remote
size_bytes      INTEGER
checksum        TEXT
created_at      TIMESTAMP

```

📌 No asumir Drive siempre → path abstracto.

---

## 7️⃣ Export (integraciones)

```sql
exports

```

```
id              UUID (PK)
job_id          UUID (FK)
provider        TEXT        -- google_drive
external_id     TEXT        -- drive file id
status          TEXT        -- pending | done | failed
error_message   TEXT
created_at      TIMESTAMP

```

👉 Permite:

- Reintentar export
- Múltiples destinos en el futuro

---

## 8️⃣ Webhook (futuro)

```sql
webhooks

```

```
id              UUID (PK)
user_id         UUID (FK)
url             TEXT
event           TEXT        -- job.completed
secret          TEXT
is_active       BOOLEAN

```

---

# 🔗 Relaciones clave (mental map)

```
User
 ├──Usage
 ├──Job
 │    ├──Article
 │    ├──JobContent
 │    ├──File
 │    └──Export

```

---

# 🚦 Índices mínimos (importantes)

- `jobs.user_id`
- `jobs.status`
- `articles.job_id`
- `usage.user_id + period`

SQLite aguanta esto sin problema.

---

# 🧠 Decisiones inteligentes (te ahorran dinero)

✔ Guardar intermedios → menos reprocesos

✔ Separar exports → reintentos baratos

✔ Job ≠ Article → escalabilidad futura

✔ Usage separado → billing simple

---

# ❌ Qué NO hacemos (todavía)

- ❌ Eventos
- ❌ Soft deletes
- ❌ Auditoría compleja
- ❌ Versionado de contenido

Todo eso viene **cuando haya usuarios**.