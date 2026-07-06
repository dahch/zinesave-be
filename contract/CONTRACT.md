# ZineSave API Contract

> Single source of truth for BE-FE communication. Last updated: 2026-07-06.
> BE repo: `zinesave-be` | FE repo: `zinesave-app`
> Primary artifact: `contract/openapi.yaml` — this doc is the human/agent-readable projection.

---

## Auth Model

- **Scheme:** JWT Bearer (HS256, 60min expiry)
- **Header:** `Authorization: Bearer <token>`
- **FE token storage:** `localStorage` key `auth-storage` (Zustand `persist` middleware)
- **Auto-logout:** FE axios interceptor triggers on ANY `401` response — clears store, redirects to `/login`
- **Public endpoints** (no auth required — explicit `security: []` in OpenAPI):
  - `GET /` — healthcheck
  - `GET /auth/google` — initiate Google login
  - `GET /auth/google/callback` — Google OAuth callback
  - `POST /auth/register` — registration
  - `POST /auth/login` — login
  - `POST /auth/verify` — email verification (token in query param)
  - `POST /auth/resend-verification` — resend verification email
  - `POST /auth/forgot-password` — request password reset
  - `POST /auth/reset-password` — reset password
  - `GET /auth/dropbox/callback` — Dropbox OAuth callback
  - `GET /auth/onedrive/callback` — OneDrive OAuth callback

---

## Job Lifecycle

```
queued → processing → done
                   ↘ failed
```

| State | Meaning |
|-------|---------|
| `queued` | Job created, waiting in arq queue for a worker |
| `processing` | Worker is executing pipeline: extract → normalize → epub generation → B2 upload. `progress` field increments 0..100 |
| `done` | EPUB generated, stored in B2, available for download via `/jobs/{id}/download` |
| `failed` | Pipeline error. Check `error_message` in raw data (not surfaced in standard JobResponse) |

**Critical:** The FE must NOT derive job completion from `progress == 100`. Only `status == "done"` means a downloadable EPUB exists. A job can be at `progress: 75` and still fail.

---

## Endpoint Index

| Method | Path | Auth | Request Body / Params | Response Schema | Key Errors |
|--------|------|------|-----------------------|-----------------|------------|
| `GET` | `/` | No | — | `HealthResponse` | — |
| `GET` | `/auth/google` | No | — | `AuthUrlResponse` | — |
| `GET` | `/auth/google/authorize` | Yes | — | `AuthUrlResponse` | 401 |
| `GET` | `/auth/google/callback` | No | `?code=` (required), `?state=` (optional) | 302 redirect | 400 |
| `POST` | `/auth/register` | No | `RegisterRequest` | `RegisterResponse` | 400, 422, 429 |
| `POST` | `/auth/login` | No | `LoginRequest` | `LoginResponse` | 401, 403, 422, 429 |
| `POST` | `/auth/verify` | No | `?token=` (query) | `VerifyResponse` | 400 |
| `POST` | `/auth/resend-verification` | No | `?email=` (query) | `ResendVerificationResponse` | 429 |
| `POST` | `/auth/forgot-password` | No | `ForgotPasswordRequest` | `ForgotPasswordResponse` | 422, 429 |
| `POST` | `/auth/reset-password` | No | `ResetPasswordRequest` | `ResetPasswordResponse` | 400, 404, 422 |
| `GET` | `/auth/dropbox/authorize` | Yes | — | `AuthUrlResponse` | 401 |
| `GET` | `/auth/dropbox/callback` | No | `?code=`, `?state=` | 302 redirect | — |
| `GET` | `/auth/onedrive/authorize` | Yes | — | `AuthUrlResponse` | 401 |
| `GET` | `/auth/onedrive/callback` | No | `?code=`, `?state=` | 302 redirect | — |
| `POST` | `/jobs` | Yes | `CreateJobRequest` | `Job` (202) | 400, 401, 402, 409, 422, 429 |
| `POST` | `/jobs/composite` | Yes | `CreateCompositeJobRequest` | `Job` (202) | 400, 401, 402, 422, 429 |
| `GET` | `/jobs` | Yes | `?page=`, `?per_page=` | `JobListResponse` | 401 |
| `GET` | `/jobs/{job_id}` | Yes | path `job_id` | `Job` | 401, 404 |
| `GET` | `/jobs/{job_id}/download` | Yes | path `job_id` | `DownloadResponse` | 401, 404 |
| `POST` | `/jobs/{job_id}/upload` | Yes | path `job_id` + `UploadRequest` | `UploadResult` | 400, 401, 404, 422 |
| `GET` | `/me` | Yes | — | `User` | 401 |
| `PUT` | `/me` | Yes | `UserUpdateRequest` | `User` | 401, 422 |
| `GET` | `/me/usage` | Yes | — | `UserUsage` | 401 |
| `GET` | `/me/dashboard` | Yes | — | `DashboardSummary` | 401 |
| `POST` | `/intentions` | Yes | `CreateIntentionRequest` | `IntentionResponse` | 401, 422 |

---

## Schema Index

| Schema | Fields | Used In |
|--------|--------|---------|
| `HealthResponse` | `status: string` | `GET /` |
| `ErrorResponse` | `message: string` | All error responses |
| `User` | `id, email, name?, plan, credits, is_beta_tester, is_active, is_company, country?, vat_number?, connected_providers[], created_at` | `GET/PUT /me` |
| `RegisterRequest` | `email, password, name, is_company?, country?, vat_number?` | `POST /auth/register` |
| `RegisterResponse` | `message: string` | `POST /auth/register` |
| `LoginRequest` | `email, password` | `POST /auth/login` |
| `LoginResponse` | `access_token, token_type` | `POST /auth/login` |
| `VerifyResponse` | `message, access_token, token_type` | `POST /auth/verify` |
| `ForgotPasswordRequest` | `email` | `POST /auth/forgot-password` |
| `ForgotPasswordResponse` | `message` | `POST /auth/forgot-password` |
| `ResetPasswordRequest` | `token, new_password` | `POST /auth/reset-password` |
| `ResetPasswordResponse` | `message` | `POST /auth/reset-password` |
| `AuthUrlResponse` | `auth_url: uri` | Google/Dropbox/OneDrive authorize |
| `Job` | `id, source_url (URL or "composite:{title}"), status (queued|processing|done|failed), progress (0-100), created_at, external_uploads: object` | `POST /jobs`, `GET /jobs/{id}`, `GET /jobs`, dashboard |
| `CreateJobRequest` | `url: uri` | `POST /jobs` |
| `CreateCompositeJobRequest` | `urls: uri[] (1-10, plan-dependent), title: string` | `POST /jobs/composite` |
| `JobListResponse` | `jobs: Job[], total, page, per_page, pages` | `GET /jobs` |
| `DownloadResponse` | `download_url: uri` | `GET /jobs/{id}/download` |
| `UploadRequest` | `provider: google_drive\|dropbox\|onedrive\|all` | `POST /jobs/{id}/upload` |
| `UploadResult` | `success: object, errors: string[]` | `POST /jobs/{id}/upload` |
| `UserUpdateRequest` | `is_company?, country?, vat_number?` (all optional) | `PUT /me` |
| `UserUsage` | `plan, credits, is_beta_tester` | `GET /me/usage`, `GET /me/dashboard` |
| `DashboardSummary` | `usage: UserUsage, recent_jobs: Job[], connected_providers: string[]` | `GET /me/dashboard` |
| `CreateIntentionRequest` | `tier_requested: string` | `POST /intentions` |
| `IntentionResponse` | `id, user_id, tier_requested, clicked_at, reward_granted: bool` | `POST /intentions` |

---

## Critical Invariants

1. **Composite jobs have internal `source_url`** — the BE stores `source_url: "composite:{title}"` and `base_url: "composite"` for composite jobs. The FE must NEVER send `url: "composite"` manually. Use `/jobs/composite` for multi-URL jobs.

2. **Download URLs are presigned and expire** — returned by `GET /jobs/{id}/download` as `download_url`. Expires after 1 hour. FE must NOT cache these URLs beyond the session. Always refetch when the user clicks "Download".

3. **Credits are awarded synchronously on intention creation** — the 5-credit reward is applied immediately within the `capture_intention` service call. However, the BE issues a DB commit, so the FE should refetch `/me` (or `/me/usage`) after capturing an intention to ensure the Zustand store reflects the new balance.

4. **All API responses must be validated with Zod** before reaching Zustand stores (FE convention). See "FE Zod Schema Hints" below.

5. **Rate limiting is active on auth and job creation endpoints** — FE must handle 429 with user-facing feedback (toast/alert). Limits: register 5/min, login 10/min, resend-verification 3/min, forgot-password 3/min, create job 10/min.

6. **Login response does NOT include the user object** — `POST /auth/login` returns only `{access_token, token_type}`. After login, the FE must separately call `GET /me` to populate the user profile in Zustand.

7. **Register does NOT auto-login** — `POST /auth/register` returns only a success message. The user must verify their email before logging in.

8. **Email verification is query-param based** — `POST /auth/verify?token=<jwt>`, NOT a JSON body. The FE must extract the token from the verification link URL.

9. **Upload `provider` accepts "all"** — sends the EPUB to every connected cloud provider. The response's `success` object maps provider names → result dicts.

10. **Connected providers are a flat string list** — `connected_providers: ["google_drive", "dropbox"]`, NOT a boolean-flag object like `{google_connected: true, dropbox_connected: false}`.

---

## Error Handling Matrix

| HTTP Code | Meaning in ZineSave | FE Expected Behavior |
|-----------|---------------------|---------------------|
| `400` | Bad request — invalid URL, hostname blocked, invalid token, email already exists | Show `detail` message to user. For URL validation errors, highlight the input field. |
| `401` | Missing or expired JWT | Axios interceptor auto-clears auth store, redirects to `/login`. No user-facing toast needed (interceptor handles it). |
| `402` | Insufficient credits (custom, not standard) | Show "You're out of credits" prompt. Offer link to `/intentions` or upgrade flow. |
| `403` | Email not verified (login blocked) | Show "Please verify your email first" with option to resend verification. |
| `404` | Job, user, or file not found | Show "Not found" message. For jobs, redirect to job list. |
| `409` | Duplicate job — same URL already queued/processing within 10 min | Show "This article is already being processed" with link to existing job. |
| `422` | Validation error (Pydantic) | Show field-level validation errors. Never silently swallow 422. |
| `429` | Rate limit exceeded | Show "Too many requests, please wait" with retry-after hint if available. |
| `500` | Internal server error | Show generic "Something went wrong" message. Log to error tracking. |

All business errors follow the structure: `{"message": "string"}`. Validate this shape with Zod before displaying. Auth errors (401) and rate-limit errors may return `{"detail": "..."}`.

---

## FE Zod Schema Hints

These match the actual BE response shapes. Validate all API responses with these before they enter Zustand stores.

```typescript
// User (GET/PUT /me response)
export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().nullable(),
  plan: z.enum(["free", "pro"]),
  credits: z.number().int().min(0),
  is_beta_tester: z.boolean(),
  is_active: z.boolean(),
  is_company: z.boolean(),
  country: z.string().nullable(),
  vat_number: z.string().nullable(),
  connected_providers: z.array(z.enum(["google_drive", "dropbox", "onedrive"])),
  created_at: z.string().datetime(),
});

// Job
export const JobSchema = z.object({
  id: z.string().uuid(),
  source_url: z.string(), // URL for single jobs, "composite:{title}" for composite
  status: z.enum(["queued", "processing", "done", "failed"]),
  progress: z.number().int().min(0).max(100),
  created_at: z.string().datetime(),
  external_uploads: z.record(z.unknown()).default({}),
});

// JobListResponse
export const JobListResponseSchema = z.object({
  jobs: z.array(JobSchema),
  total: z.number().int(),
  page: z.number().int(),
  per_page: z.number().int(),
  pages: z.number().int(),
});

// LoginResponse
export const LoginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.literal("bearer"),
});

// DownloadResponse
export const DownloadResponseSchema = z.object({
  download_url: z.string().url(),
});

// UploadResult
export const UploadResultSchema = z.object({
  success: z.record(z.unknown()),
  errors: z.array(z.string()),
});

// UserUsage
export const UserUsageSchema = z.object({
  plan: z.enum(["free", "pro"]),
  credits: z.number().int(),
  is_beta_tester: z.boolean(),
});

// DashboardSummary
export const DashboardSummarySchema = z.object({
  usage: UserUsageSchema,
  recent_jobs: z.array(JobSchema),
  connected_providers: z.array(z.enum(["google_drive", "dropbox", "onedrive"])),
});

// IntentionResponse
export const IntentionResponseSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  tier_requested: z.string(),
  clicked_at: z.string().datetime(),
  reward_granted: z.boolean(),
});

// ErrorResponse (universal error shape)
export const ErrorResponseSchema = z.object({
  message: z.string(),
});
```

**CreateJobRequest (FE → BE):**
```typescript
export const CreateJobRequestSchema = z.object({
  url: z.string().url(),
});
```

**CreateCompositeJobRequest (FE → BE):**
```typescript
export const CreateCompositeJobRequestSchema = z.object({
  urls: z.array(z.string().url()).min(1).max(10), // plan-dependent: max 4 (free), 10 (pro)
  title: z.string().min(1),
});
```

---

## BE Pydantic Hints

For reference when the BE agent needs to verify existing schemas match the contract.

```python
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    plan: str
    credits: int
    is_beta_tester: bool
    is_active: bool
    is_company: bool
    country: str | None
    vat_number: str | None
    connected_providers: list[str] = []
    created_at: datetime

class JobResponse(BaseModel):
    id: str
    source_url: str
    status: str  # queued | processing | done | failed
    progress: int
    created_at: datetime
    external_uploads: dict = {}

class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    per_page: int
    pages: int

class JobCreate(BaseModel):
    url: HttpUrl

class JobCompositeCreate(BaseModel):
    urls: list[HttpUrl]
    title: str

class Register(BaseModel):
    email: str
    password: str
    name: str
    is_company: bool = False
    country: str | None = None
    vat_number: str | None = None

class Login(BaseModel):
    email: str
    password: str

class ForgotPassword(BaseModel):
    email: str

class ResetPassword(BaseModel):
    token: str
    new_password: str

class UserUpdate(BaseModel):
    is_company: bool | None = None
    country: str | None = None
    vat_number: str | None = None

class IntentionCreate(BaseModel):
    tier_requested: str

class IntentionResponse(BaseModel):
    id: str
    user_id: str
    tier_requested: str
    clicked_at: datetime
    reward_granted: bool

# Inline in routes/upload.py — not in domain/schemas/
class UploadRequest(BaseModel):
    provider: str  # google_drive | dropbox | onedrive | all
```

---

## Changelog

### 2026-07-06
- [CHANGED] `ErrorResponse`: field renamed `detail` → `message` to match actual DomainException handler output
- [CHANGED] `Job.source_url`: removed `format: uri` (composite jobs store `"composite:{title}"`), added description
- [CHANGED] `CreateCompositeJobRequest.urls`: `minItems` 2→1, `maxItems` 20→10, added description about plan-dependent limits
- [CHANGED] `/jobs/composite` endpoint description: clarified URL range 1-10, plan-dependent
- [REMOVED] `MessageResponse` schema: unreferenced in code, removed to match source

