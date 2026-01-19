# Arquitectura SaaS Completa

Tipo: Arquitectura
Estado: Completado
Fecha de creación: 25 de diciembre de 2025
Última actualización: 25 de diciembre de 2025

# 🧠 Principios base (importantes)

Antes de tecnología, 5 reglas que vamos a seguir:

1. **Un solo backend core**
2. **Separación lógica, no infra pesada**
3. **Async desde el día 1**
4. **Pagar solo cuando haya usuarios**
5. **Nada que no puedas mantener solo**

---

# 🏗️ Arquitectura SaaS – Fase Bootstrap (0–50€ / mes)

## Vista general

```
[ Cliente ]
   │
   ▼
[ FastAPI ]
   ├── Auth + API
   ├── Orquestador
   └── Background Tasks
          │
          ▼
[ Processor ]
   ├── Reader Mode
   ├── HTML Normalizer
   ├── ePub Generator
   └── Exporters (Drive)
          │
          ▼
[ Storage ]
   ├── Local FS
   └── Google Drive

```

👉 Todo corre **en un solo servidor** inicialmente.

---

## 1️⃣ Backend Core

### Stack

- **FastAPI**
- **Python 3.12**
- **Uvicorn**
- **Pydantic v2**

### Responsabilidades

- Auth
- Rate limiting
- API pública
- Gestión de jobs
- Webhooks futuros

📌 Sin microservicios todavía.

---

## 2️⃣ Procesamiento async (sin Redis al inicio)

### Opción 0-coste (inicial)

Usar **BackgroundTasks** de FastAPI:

```python
from fastapi import BackgroundTasks

@router.post("/generate")
def generate(cmd: GenerateCmd, bg: BackgroundTasks):
    bg.add_task(process_url, cmd)
    return {"status": "queued"}

```

✔ Cero infraestructura

❌ No persistente si el server cae

👉 Perfecto para MVP privado.

---

### Evolución barata (cuando crezca)

- **SQLite + RQ**
- Redis en:
    - Fly.io
    - Railway
    - Upstash (free tier)

💡 **No se necesita el día 1.**

---

## 3️⃣ Dominio (Clean Architecture)

```
/domain
  ├── entities
  │   ├── Article
  │   ├── Book
  │   └── Job
  ├── services
  │   ├── ReaderService
  │   └── EpubService
  └── ports
      ├── StoragePort
      └── ExportPort

```

Ventaja:

- Cambias Drive → Kindle
- Cambias EPUB → PDF
- Sin tocar el core

---

## 4️⃣ Base de datos (low cost)

### Inicio

- **SQLite**
- Archivo local

Datos:

- Usuarios
- Jobs
- Estado
- Metadatos

### Futuro

- Migrar a **PostgreSQL** sin dolor

---

## 5️⃣ Auth (simple pero segura)

### MVP

- Email + magic link
- OAuth Google (inicialmente necesario)

Librerías:

- `fastapi-users`
- JWT corto
- Refresh tokens simples

📌 Evita passwords al inicio.

---

## 6️⃣ Almacenamiento de archivos

### Fase 1

- **Filesystem local**
- Limpieza con cron interno

### Fase 2

- Google Drive del usuario
- S3-compatible cuando haya dinero

---

## 7️⃣ API pública (pensada para extensiones)

```
POST   /jobs
GET    /jobs/{id}
GET    /jobs/{id}/download

```

Estados:

- queued
- processing
- done
- failed

---

## 8️⃣ Observabilidad (gratis)

- Logs estructurados
- Sentry (free tier)
- Métricas básicas

📌 Nada de Prometheus aún.

---

## 9️⃣ Infraestructura barata

### Recomendado

- **Fly.io**
- **Railway**
- **Hetzner Cloud (5€ VPS)**

👉 Hetzner gana en coste fijo bajo.

---

## 10️⃣ Seguridad mínima viable

- Rate limit por IP
- Límite de URLs por usuario
- Sanitización HTML
- Timeouts

---

# 🔮 Evolución natural (cuando haya tracción)

```
[ API ]
    |
[ Queue ]
    |
[ Worker Pool ]

```

- Redis
- Workers separados
- Postgres
- Stripe
- Planes:
    - Free: 5 artículos / mes
    - Pro: ilimitado
    - Team

---

# 💰 Coste estimado inicial

| Recurso | Coste |
| --- | --- |
| VPS | 5–10 € |
| Dominio | ya lo tienes |
| Google API | gratis |
| Sentry | gratis |
| Redis | 0 € |

➡️ **~10€ / mes**

---

# 🧩 Decisión clave que te ahorra dinero

👉 **NO microservicios**

👉 **NO Kubernetes**

👉 **NO colas distribuidas al inicio**

Eso viene **cuando empiece a facturar**, no antes.