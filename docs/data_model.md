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
name            String
password_hash   String
is_verified     Boolean
credits         Integer
created_at      DateTime
updated_at      DateTime
```

### Decisiones importantes

- ✔ Soporte de login nativo (`password_hash`) y validación de correo (`is_verified`).
- ✔ `credits` incrustado para control rápido del rate limit, recargado a través de compras (`Intentions`).
- ✔ Conexiones de nube abstraídas a otra tabla (`cloud_connections`).

---

## 2️⃣ Intention (Créditos y Compras)

```sql
intentions
```

```
id              String (PK)
user_id         String (FK)
credits_to_add  Integer
amount_cents    Integer
currency        String
status          String      -- pending | completed | failed
created_at      DateTime
updated_at      DateTime
```

📌 **Por qué existe:** Permite llevar un registro auditable de intenciones de recarga, compras vía Stripe u otros proveedores, separando el saldo actual del usuario (User) del historial transaccional.

---

## 3️⃣ CloudConnection (Exportaciones externas)

```sql
cloud_connections
```

```
id              String (PK)
user_id         String (FK)
provider        String      -- google_drive | dropbox | onedrive
access_token    String
refresh_token   String
expiry          DateTime
metadata        JSONB
created_at      DateTime
```

👉 Separa las credenciales OAuth externas del modelo de usuario, permitiendo a los usuarios enlazar múltiples cuentas de nubes externas.

---

## 4️⃣ Job (corazón del sistema)

```sql
jobs
```

```
id              String (PK)
user_id         String (FK)
source_url      String
base_url        String
status          String      -- pending | processing | completed | failed
progress        Integer     -- 0-100
error_message   String

created_at      DateTime
started_at      DateTime
finished_at     DateTime
```

### Claves

- ✔ `error_message` para feedback de UX y debug.
- ❌ No se guardan archivos binarios aquí, usamos la tabla `File` o storage externo (Backblaze).

---

## 5️⃣ Article / Metadata (contenido lógico futuro)
Actualmente integrado parcialmente o no modelado explícitamente como una tabla aislada más allá de `job_contents` si se procesan capítulos múltiples, pero los metadatos generados se pueden agregar a futuro para tener un histórico independiente del trabajo.

---

## 6️⃣ File (outputs / ePub)

```sql
files
```

```
id              String (PK)
job_id          String (FK)
user_id         String (FK)
filename        String
size_bytes      Integer
storage_path    String
content_type    String      -- application/epub+zip
created_at      DateTime
```

📌 `storage_path` asume almacenamiento remoto genérico (B2) para descargar, independientemente de la exportación a Google Drive u otros.

---

# 🔗 Relaciones clave (mental map)

```
User
 ├──CloudConnection (0..N)
 ├──Intention (0..N)
 ├──Job (0..N)
 │    └──File (1..N)
```

---

# 🛡️ Patrón Repositorio (Clean Architecture)

Las rutas de FastAPI (y los Servicios) **no interactúan directamente con SQLAlchemy ni con estos modelos de datos**.

Para cada entidad, existe una clase en `app/domain/repositories/` (e.g. `UserRepository`, `JobRepository`) que expone los métodos CRUD abstractos:
- Ventaja 1: Se oculta el código SQL / SQLAlchemy.
- Ventaja 2: Permite hacer tests mediante `unittest.mock.Mock` sin requerir base de datos de testeo.