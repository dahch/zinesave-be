# API Contract

Tipo: API Contract
Estado: Completado
Fecha de creación: 25 de diciembre de 2025
Última actualización: 25 de diciembre de 2025

# 📘 API Contract – v1

**Base URL**

```
/api/v1

```

---

## 1️⃣ Autenticación

### 🔐 Auth strategy (MVP)

- OAuth Google (obligatorio para Drive)
- JWT short-lived
- Refresh token

---

### POST `/auth/google`

Intercambia `authorization_code` por JWT.

**Request**

```json
{
  "code": "google_oauth_code"
}

```

**Response 200**

```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "expires_in": 3600
}

```

---

### POST `/auth/refresh`

```json
{
  "refresh_token": "jwt"
}

```

---

## 2️⃣ Jobs (core del producto)

### 📌 Crear Job (URL → ePub)

### POST `/jobs`

**Request**

```json
{
  "url": "https://blog.example.com/article",
  "output": "epub",
  "export": {
    "type": "google_drive",
    "folder_id": "optional"
  }
}

```

**Validaciones**

- URL válida
- Dominio permitido
- Límite por plan

**Response 202**

```json
{
  "job_id": "job_123",
  "status": "queued"
}

```

---

### 📌 Obtener estado del Job

### GET `/jobs/{job_id}`

**Response 200**

```json
{
  "id": "job_123",
  "status": "processing",
  "progress": 65,
  "created_at": "2025-01-01T12:00:00Z",
  "finished_at": null,
  "error": null}

```

---

### 📌 Descargar archivo (si no se exporta)

### GET `/jobs/{job_id}/download`

**Response**

- `200 application/epub+zip`
- `404` si no está listo

---

### 📌 Listar jobs del usuario

### GET `/jobs`

Query params:

```
?status=done
?limit=20
?offset=0

```

---

## 3️⃣ Artículos (resultado lógico)

### GET `/articles/{article_id}`

```json
{
  "id": "art_123",
  "title": "Cómo diseñar APIs",
  "author": "John Doe",
  "word_count": 1345,
  "language": "es",
  "source_url": "https://...",
  "created_at": "..."
}

```

📌 No es obligatorio para MVP, pero **sí importante para futuro**.

---

## 4️⃣ Usuario

### GET `/me`

```json
{
  "id": "user_123",
  "email": "daniel@gmail.com",
  "plan": "free",
  "usage": {
    "jobs_used": 3,
    "jobs_limit": 5
  }
}

```

---

## 5️⃣ Límites y errores (SaaS-ready)

### Errores estándar

```json
{
  "error": {
    "code": "LIMIT_REACHED",
    "message": "Monthly job limit reached"
  }
}

```

Códigos:

- `INVALID_URL`
- `LIMIT_REACHED`
- `PROCESSING_ERROR`
- `EXPORT_FAILED`
- `UNAUTHORIZED`

---

## 6️⃣ Webhooks (Futuro, pero definidos)

### POST `/webhooks/job-completed`

```json
{
  "job_id": "job_123",
  "status": "done",
  "download_url": "..."
}

```

---

## 7️⃣ Versionado (CRÍTICO)

- `/api/v1`
- Cambios grandes → `/v2`
- Nunca romper contratos existentes

---

# 🧩 DTOs principales (mental model)

```tsx
User
Job
Article
Export
Usage

```

---

## 🎯 Decisiones importantes (por qué así)

- **Jobs asíncronos** → escalan
- **202 Accepted** → correcto semánticamente
- **Export desacoplado** → Drive / Kindle / S3
- **Jobs separados de Articles** → futuro multi-capítulo
- **/me** → billing fácil