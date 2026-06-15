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
- **Python 3.12**
- **Uvicorn**
- **Pydantic v2 / Pydantic-Settings**

### Responsabilidades

- Auth (Google OAuth, JWT, Magic Links)
- Rate limiting (`slowapi`)
- API pública
- Gestión de créditos (Intentions)
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

- Email + Password (JWT)
- OAuth Google (Sincroniza Drive)
- Dropbox / OneDrive OAuth
- Verificación de email y Reset de contraseña.

Librerías:
- `passlib` (Argon2)
- `python-jose` (JWT)
- `google-auth-oauthlib`

---

## 6️⃣ Almacenamiento de archivos

- **Backblaze B2**: Sistema de almacenamiento principal de objetos compatible con S3.
- **Exportaciones externas**: El usuario puede vincular Google Drive, Dropbox y OneDrive para mandar copias automáticas.

---

## 7️⃣ API pública

```
POST   /jobs
GET    /jobs/{id}
GET    /jobs
GET    /upload/download/{file_id}
POST   /me/intentions (Compra de créditos)
```

Estados de un Job:
- `pending`
- `processing`
- `completed`
- `failed`

---

## 8️⃣ Observabilidad y Logs

- **JSON Logging estructurado:** Implementado en `app/core/logging.py` para compatibilidad máxima con Datadog o Elastic.
- **Sentry SDK:** Integrado para capturar excepciones del dominio y errores de servidor no controlados.

---

## 9️⃣ Infraestructura

- Base de datos relacional (PostgreSQL)
- Servidor caché y colas (Redis)
- Storage (Backblaze B2)
- Worker (Python Arq)
- API (FastAPI)

---

## 10️⃣ Seguridad

- Limitación de tasa de solicitudes (Rate Limiting)
- SSRF Protection: Las URLs a procesar se validan internamente bloqueando rangos IP locales y meta-endpoints (AWS/GCP metadata).
- Pydantic-Settings centraliza los secretos desde el `.env`.