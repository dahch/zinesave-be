# AI_CONTEXT.md - Reader to EPUB Converter (ZineSave)

## Project Overview
This project is a FastAPI-based API designed to convert web content (articles, URLs) into EPUB format. It features a background processing system (Arq + Redis) for handling conversions asynchronously, a credits/purchase-intentions system, cloud storage integration (B2), and optional manual export to Google Drive, Dropbox, and OneDrive.

- **Primary Technologies:** Python 3.11, FastAPI, SQLAlchemy (PostgreSQL), Redis (arq), Backblaze B2 (boto3).
- **Secondary Technologies:** Sentry (monitoring), MailerSend (emails), Google/Dropbox/OneDrive OAuth (auth & cloud export).
- **Deployment:** Fly.io (app: `zinesave-be`, region: `ams`), CI/CD via GitHub Actions.
- **Architecture:** Clean Architecture principles with strict separation into:
  - **API Routes:** Lightweight HTTP endpoints (`app/api/routes`).
  - **Dependencies:** Centralized injection of services (`app/api/dependencies/services.py`).
  - **Services:** Pure business logic (`app/services`).
  - **Repositories:** Data access layer isolating SQLAlchemy (`app/domain/repositories`).
  - **Domain:** Data models (SQLAlchemy) and schemas (Pydantic v2).
  - Background tasks are handled by `arq`.

## Building and Running

### Prerequisites
- Python 3.11+
- Redis (for background jobs)
- PostgreSQL (database)
- Backblaze B2 account (for EPUB storage)

### Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
See `app/core/config.py` for full list. Required vars:
`FRONTEND_URL`, `BACKEND_URL`, `DATABASE_URL`, `JWT_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_PROJECT_ID`.

### Running the API
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.

### Running the Background Worker
```bash
arq app.worker.WorkerSettings
```

### Using Docker
```bash
# Start Redis
docker-compose up -d redis

# Build and start the worker
docker-compose up -d --build worker
```

### Testing
```bash
# Run tests with coverage (minimum 70%)
pytest tests/ --cov=app --cov-fail-under=70
```

## Directory Structure
- `app/`: Main application code.
    - `api/`: FastAPI routes (`auth`, `intentions`, `jobs`, `me`, `upload`) and dependencies.
    - `core/`: Core configurations (database, logging via JSON, queue, security).
    - `domain/`: Data models (SQLAlchemy) and schemas (Pydantic), plus interface-like Repositories.
    - `services/`: Business logic services (Auth, EPUB generation, jobs, intentions, upload, cloud export, retention, etc.).
- `docs/`: Project documentation (architecture, API contract, data model, pipeline).
- `scripts/`: Maintenance and migration scripts.
- `tests/`: Project tests with unit tests and repository mocks.

## Key Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/auth/google` | Initiate Google OAuth |
| GET | `/auth/google/callback` | Google OAuth callback |
| POST | `/auth/register` | Register with email/password |
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/verify` | Verify email via token |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |
| GET | `/auth/dropbox/authorize` | Initiate Dropbox OAuth |
| GET | `/auth/onedrive/authorize` | Initiate OneDrive OAuth |
| POST | `/jobs` | Create conversion job (single URL) |
| POST | `/jobs/composite` | Create composite job (multiple URLs) |
| GET | `/jobs` | List jobs (paginated: ?page=1&per_page=20) |
| GET | `/jobs/{id}` | Get job status |
| GET | `/jobs/{id}/download` | Get presigned download URL |
| POST | `/jobs/{id}/upload` | Upload EPUB to cloud provider |
| GET | `/me` | Get user profile |
| PUT | `/me` | Update user profile |
| GET | `/me/usage` | Get credits/plan info |
| GET | `/me/dashboard` | Get dashboard summary |
| POST | `/intentions` | Capture purchase intention (rewards 5 credits) |
| GET | `/` | Healthcheck |

## Development Conventions
- **Clean Architecture & Repository Pattern:** Keep business logic strictly in `app/services`. Database logic MUST be handled in `app/domain/repositories`. API routes must only act as IO controllers.
- **Dependency Injection:** Inject repositories and external clients into services. Inject services into routes via `app/api/dependencies/services.py`.
- **Async Processing:** Use `arq` for long-running tasks. Trigger them from `QueueService` and process them in `app/worker.py`. The pipeline function `run_pipeline` runs synchronously in a thread executor.
- **Validation:** Use Pydantic v2 for request/response validation, schemas, and environment configuration (`app/core/config.py`).
- **Observability:** Use structured JSON logging (`app/core/logging.py`) and Sentry for error tracking (both API and worker).
- **Auth:** JWT tokens (PyJWT, HS256, 60min expiry). Reset tokens (15min expiry). Argon2 via passlib for passwords.
- **Rate Limiting:** slowapi with in-memory storage (no Redis, saves Upstash commands).
- **Testing:** TDD mindset. Add tests in the `tests/` directory for any new logic. Use `unittest.mock.Mock` to isolate services from their repository dependencies. Target minimum 70% coverage.
- **Job Statuses:** `queued` → `processing` → `done` / `failed`.
- **Composite Jobs:** Created via `POST /jobs/composite`. Pipeline detects `base_url == "composite"`. Per-URL results stored as `JobContent` with indexed steps (`extracted_0`, `normalized_1`).
- **Cloud Export:** Manual only (`POST /jobs/{id}/upload`). Not automatic during pipeline.
- **Retention:** Cron job at 03:00 UTC deletes files from free-tier users older than 7 days.
