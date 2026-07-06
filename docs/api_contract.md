# API Contract

Tipo: API Contract
Estado: Actualizado
Fecha de creación: 25 de diciembre de 2025
Última actualización: 6 de julio de 2026

# 📘 API Contract – v1

**Base URL**

No hay prefijo `/api/v1`. Las rutas se montan directamente en la raíz (ej. `/auth/login`, `/jobs`).

---

## 1️⃣ Autenticación (`/auth`)

### Auth strategy

- Login nativo con email + password (JWT, Argon2)
- Google OAuth (login y bind de cuenta)
- Dropbox / OneDrive OAuth (solo bind de cuenta para exportación)
- Verificación de email
- Forgot / Reset password

---

### GET `/auth/google`

Inicia el flujo OAuth de Google. Devuelve la URL de autorización de Google.

**Response 200**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

---

### GET `/auth/google/authorize`

Similar a `/auth/google` pero requiere autenticación. Se usa para **vincular** Google Drive a una cuenta existente.

**Requires:** Bearer token
**Response 200**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

---

### GET `/auth/google/callback`

Callback del flujo OAuth de Google. Si hay `state` (token JWT), vincula Drive a la cuenta existente. Si no, hace login o registro.

**Query params:** `?code=...&state=...` (state opcional)

**Response:** Redirect a `{FRONTEND_URL}/auth/callback?token={jwt}` o `{FRONTEND_URL}/dashboard/account`

---

### POST `/auth/register`

Registro con email y password.

**Rate limit:** 5/min

**Request**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe",
  "is_company": false,
  "country": "ES",
  "vat_number": null
}
```

**Response 200**
```json
{
  "message": "Registration successful. Please check your email to verify your account."
}
```

---

### POST `/auth/login`

**Rate limit:** 10/min

**Request**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response 200**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

---

### POST `/auth/verify`

Verifica el email de un usuario mediante token JWT.

**Body param:** `token` (string)

**Response 200**
```json
{
  "message": "Email verified successfully",
  "access_token": "new_jwt_token",
  "token_type": "bearer"
}
```

---

### POST `/auth/resend-verification`

**Rate limit:** 3/min

Reenvía el email de verificación.

**Body param:** `email` (string)

**Response 200**
```json
{
  "message": "If the email is registered and not yet verified, a verification link has been sent."
}
```

---

### POST `/auth/forgot-password`

**Rate limit:** 3/min

**Request**
```json
{
  "email": "user@example.com"
}
```

**Response 200**
```json
{
  "message": "If the email is registered, a password reset link has been sent."
}
```

---

### POST `/auth/reset-password`

**Request**
```json
{
  "token": "reset_jwt_token",
  "new_password": "new_secure_password"
}
```

**Response 200**
```json
{
  "message": "Password updated successfully"
}
```

---

### GET `/auth/dropbox/authorize`

Requiere autenticación. Devuelve URL de autorización de Dropbox para vincular cuenta.

**Response 200**
```json
{
  "auth_url": "https://www.dropbox.com/oauth2/authorize?..."
}
```

---

### GET `/auth/dropbox/callback`

Callback OAuth de Dropbox.

**Query params:** `?code=...&state=...`

**Response:** Redirect a `{FRONTEND_URL}/dashboard/account`

---

### GET `/auth/onedrive/authorize`

Requiere autenticación. Devuelve URL de autorización de OneDrive.

**Response 200**
```json
{
  "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?..."
}
```

---

### GET `/auth/onedrive/callback`

Callback OAuth de OneDrive.

**Query params:** `?code=...&state=...`

**Response:** Redirect a `{FRONTEND_URL}/dashboard/account`

---

## 2️⃣ Jobs (`/jobs`)

### POST `/jobs`

Crear un trabajo de conversión (URL → EPUB).

**Rate limit:** 10/min

**Request**
```json
{
  "url": "https://blog.example.com/article"
}
```

**Response 202**
```json
{
  "id": "job_uuid",
  "source_url": "https://blog.example.com/article",
  "status": "queued",
  "progress": 0,
  "created_at": "2025-01-01T12:00:00",
  "external_uploads": {}
}
```

---

### POST `/jobs/composite`

Crear un trabajo compuesto (múltiples URLs → un EPUB).

**Rate limit:** 10/min

**Request**
```json
{
  "urls": [
    "https://blog.example.com/article-1",
    "https://blog.example.com/article-2"
  ],
  "title": "My Collection"
}
```

**Validaciones:** Máximo 4 URLs para plan free, 10 para pro.

**Response 202** (mismo schema que POST /jobs)

---

### GET `/jobs`

Listar trabajos del usuario autenticado (paginado).

**Query params:**
- `page`: Número de página (default: 1)
- `per_page`: Items por página (default: 20, max: 100)

**Response 200**
```json
{
  "jobs": [
    {
      "id": "job_uuid",
      "source_url": "https://...",
      "status": "done",
      "progress": 100,
      "created_at": "2025-01-01T12:00:00",
      "external_uploads": {}
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### GET `/jobs/{job_id}`

Obtener estado de un trabajo.

**Response 200**
```json
{
  "id": "job_uuid",
  "source_url": "https://...",
  "status": "processing",
  "progress": 50,
  "created_at": "2025-01-01T12:00:00",
  "external_uploads": {}
}
```

**Errores:** `404` si no existe o no pertenece al usuario.

---

### GET `/jobs/{job_id}/download`

Obtener URL de descarga del EPUB generado.

**Response 200**
```json
{
  "download_url": "https://b2-bucket.s3.amazonaws.com/epubs/job_uuid.epub?Signature=..."
}
```

**Errores:** `400` si el archivo no está listo o expiró.

---

### POST `/jobs/{job_id}/upload`

Subir manualmente un EPUB completado a servicios cloud conectados.

**Request**
```json
{
  "provider": "google_drive"
}
```

`provider` puede ser: `google_drive`, `dropbox`, `onedrive` o `all` (todos los conectados).

**Response 200**
```json
{
  "success": {
    "google_drive": {"id": "file_id", "name": "article.epub"}
  },
  "errors": []
}
```

---

## 3️⃣ Usuario (`/me`)

### GET `/me`

**Response 200**
```json
{
  "id": "user_uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "plan": "free",
  "credits": 5,
  "is_beta_tester": true,
  "is_active": true,
  "is_company": false,
  "country": null,
  "vat_number": null,
  "connected_providers": ["google_drive"],
  "created_at": "2025-01-01T12:00:00"
}
```

---

### PUT `/me`

Actualizar perfil.

**Request**
```json
{
  "is_company": true,
  "country": "ES",
  "vat_number": "ES12345678Z"
}
```

Todos los campos son opcionales.

**Response 200** (mismo schema que GET /me)

---

### GET `/me/usage`

Obtener información de uso y plan.

**Response 200**
```json
{
  "plan": "free",
  "credits": 5,
  "is_beta_tester": true
}
```

---

### GET `/me/dashboard`

Obtener resumen del dashboard: uso, jobs recientes y conexiones.

**Response 200**
```json
{
  "usage": {
    "plan": "free",
    "credits": 5,
    "is_beta_tester": true
  },
  "recent_jobs": [
    {
      "id": "job_uuid",
      "source_url": "https://...",
      "status": "done",
      "progress": 100,
      "created_at": "2025-01-01T12:00:00",
      "external_uploads": {}
    }
  ],
  "connected_providers": ["google_drive"]
}
```

---

## 4️⃣ Intentions (`/intentions`)

### POST `/intentions`

Capturar intención de compra de un plan. Al crear, otorga 5 crédidos como recompensa.

**Request**
```json
{
  "tier_requested": "pro"
}
```

**Response 200**
```json
{
  "id": "intention_uuid",
  "user_id": "user_uuid",
  "tier_requested": "pro",
  "clicked_at": "2025-01-01T12:00:00",
  "reward_granted": true
}
```

Si ya existe una intención para ese usuario y tier, `reward_granted` será `false`.

---

## 5️⃣ Errores

### Errores estándar

Todos los errores se devuelven como:

```json
{
  "message": "Description of the error"
}
```

**Códigos HTTP usados:**
- `400` — Error de validación o de negocio
- `401` — No autenticado o token inválido
- `403` — Email no verificado
- `404` — Recurso no encontrado
- `429` — Rate limit excedido

### Excepciones de dominio

| Condición | HTTP | Message |
|---|---|---|
| Email ya registrado | 400 | `Email already exists` |
| Credenciales inválidas | 401 | `Invalid credentials` |
| Email no verificado | 403 | `Email not verified` |
| Usuario no encontrado | 404 | `User not found` |
| Token inválido/expirado | 400 | `Invalid or expired token` |
| Créditos insuficientes | 400 | `INSUFFICIENT_CREDITS` |
| URL inválida/bloqueada | 400 | `URL resolves to a blocked IP range` |
| Job duplicado reciente | 400 | `A job for this URL is already in progress` |

---

## 6️⃣ Estados del Job

| Estado | Significado |
|---|---|
| `queued` | Creado, esperando ser procesado por Arq |
| `processing` | El pipeline está ejecutándose |
| `done` | Completado exitosamente |
| `failed` | Error durante el procesamiento |

---

## 7️⃣ Healthcheck

### GET `/`

**Response 200**
```json
{
  "status": "ok"
}
```
