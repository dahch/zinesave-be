# Arquitectura SaaS Completa

Tipo: Arquitectura
Estado: Completado
Fecha de creación: 25 de diciembre de 2025
Última actualización: 16 de junio de 2026

# 🧠 Principios base (importantes)

Antes de tecnología, 5 reglas que vamos a seguir:

1. **Un solo backend core**
2. **Separación lógica, no infra pesada**
3. **Async desde el día 1**
4. **Pagar solo cuando haya usuarios**
5. **Nada que no puedas mantener solo**

---

# 🏗️ Arquitectura SaaS – Fase Actual

## Vista general

```
[ Cliente ]
   │
   ▼
[ FastAPI ]
   ├── Auth + API Routes (IO Controllers)
   └── Dependency Injection (services.py)
          │
          ▼
[ Services (Clean Architecture) ]
   ├── AuthService, UserService
   ├── JobService, IntentionService
   ├── UploadService, PipelineService
   └── Exporters (Drive, Dropbox, OneDrive)
          │
          ▼
[ Domain / Repositories ]  <---> [ Worker (Arq + Redis) ]
   ├── UserRepository               │
   ├── JobRepository                ├── Reader Mode
   ├── IntentionRepository          ├── HTML Normalizer
   └── CloudConnectionRepository    └── ePub Generator
          │
          ▼
[ Storage & Data ]
   ├── PostgreSQL (SQLAlchemy)
   └── Backblaze B2 (Object Storage)

```

👉 La API delega trabajo pesado a **Arq** mediante **Redis**.

---

## 1️⃣ Backend Core

### Stack

- **FastAPI**
- **Python 3.11**
- **Uvicorn**
- **Pydantic v2 / Pydantic-Settings**

### Responsabilidades

- Auth (Google OAuth, Dropbox OAuth, OneDrive OAuth, JWT)
- Rate limiting (`slowapi`, in-memory, sin Redis)
- API pública
- Gestión de créditos e intenciones de compra (Intentions)
- Encolamiento de jobs (vía `QueueService`)

📌 La capa de rutas (`app/api/routes/`) no toca la base de datos directamente, todo se inyecta.

---

## 2️⃣ Procesamiento async (Redis + Arq)

Se implementó **Arq** apoyado por **Redis** para manejar las tareas en segundo plano garantizando persistencia y escalabilidad.

```python
await self.queue_service.enqueue_job("execute_pipeline", job.id)
```

✔ Escalable: Worker corre en proceso separado (`app/worker.py`).
✔ Persistente: Los jobs no se pierden si el servidor API cae.

---

## 3️⃣ Dominio y Clean Architecture

```
/app
  ├── api/
  │   ├── dependencies/ (Inyección de dependencias)
  │   └── routes/       (Controladores HTTP)
  ├── core/             (Configuración, JSON Logging, Security)
  ├── domain/
  │   ├── models/       (SQLAlchemy)
  │   ├── repositories/ (Aislamiento de DB)
  │   └── schemas/      (Pydantic)
  └── services/         (Lógica de negocio pura)
```

Ventaja:
- Lógica de negocio (Services) es agnóstica a SQLAlchemy.
- Testing unitario usando repositorios simulados (mocks) es trivial.
- Cambiar de BD o añadir proveedores de la nube no afecta el Core.

---

## 4️⃣ Base de datos

- **PostgreSQL** mediante SQLAlchemy.
- Aislado de los servicios mediante el **Patrón Repositorio**.

Datos:
- Users & Auth (incluye Cloud Connections)
- Jobs
- Intentions (Créditos / Compras)
- Files

---

## 5️⃣ Auth (simple pero segura)

### Implementado

- Email + Password (JWT, con verificación de email)
- Google OAuth (login y bind de Google Drive)
- Dropbox / OneDrive OAuth (bind para exportación)
- Forgot / Reset de contraseña
- Welcome email para usuarios OAuth

Librerías:
- `passlib` (Argon2)
- `PyJWT` (JWT)
- `google-auth-oauthlib`

---

## 6️⃣ Almacenamiento de archivos

- **Backblaze B2**: Sistema de almacenamiento principal de objetos compatible con S3.
- **Exportaciones externas**: El usuario puede vincular Google Drive, Dropbox y OneDrive para mandar copias automáticas.

---

## 7️⃣ API pública

```
POST   /jobs                     (Crear job simple)
POST   /jobs/composite           (Crear job compuesto multi-URL)
GET    /jobs                     (Listar jobs, paginado: ?page=1&per_page=20)
GET    /jobs/{id}                (Estado del job)
GET    /jobs/{id}/download       (Presigned URL de descarga)
POST   /jobs/{id}/upload         (Subir a cloud manualmente)
GET    /me                       (Perfil del usuario)
PUT    /me                       (Actualizar perfil)
GET    /me/usage                 (Uso y créditos)
GET    /me/dashboard             (Dashboard completo)
POST   /intentions               (Capturar intención de compra)
```

Estados de un Job:
- `queued` — creado, esperando worker
- `processing` — pipeline en ejecución
- `done` — completado
- `failed` — error en el procesamiento

---

## 8️⃣ Observabilidad y Logs

- **JSON Logging estructurado:** Implementado en `app/core/logging.py` para compatibilidad máxima con Datadog o Elastic.
- **Sentry SDK:** Integrado en API y Worker para capturar excepciones del dominio y errores de servidor no controlados.

---

## 9️⃣ Infraestructura

- **API:** FastAPI + Uvicorn
- **Worker:** Arq (procesamiento asíncrono de conversiones)
- **Cola:** Redis
- **Base de datos:** PostgreSQL
- **Storage:** Backblaze B2 (S3-compatible)
- **Email:** MailerSend (verificación, reset password, welcome)
- **Monitoreo:** Sentry
- **Despliegue:** Fly.io (app `zinesave-be`, región `ams`), CI/CD con GitHub Actions

El `fly.toml` define dos procesos:
- `app`: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- `worker`: `arq app.worker.WorkerSettings`

---

## 10️⃣ Retención Automática

El worker ejecuta un cron job diario (03:00 UTC) que elimina archivos EPUB de usuarios en plan free con más de 7 días de antigüedad. Implementado en `app/services/retention_service.py`.

---

## 11️⃣ Seguridad

- Limitación de tasa de solicitudes (Rate Limiting)
- SSRF Protection: Las URLs a procesar se validan internamente bloqueando rangos IP locales y meta-endpoints (AWS/GCP metadata).
- Pydantic-Settings centraliza los secretos desde el `.env`.