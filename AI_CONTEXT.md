# AI_CONTEXT.md - Reader to EPUB Converter

## Project Overview
This project is a FastAPI-based API designed to convert reader content (articles, URLs, etc.) into EPUB format. It features a background processing system for handling conversions asynchronously and integrates with cloud storage for file management.

- **Primary Technologies:** Python 3.12, FastAPI, SQLAlchemy (PostgreSQL), Redis (arq), Backblaze B2 (boto3).
- **Secondary Technologies:** Sentry (monitoring), MailerSend (emails), Google OAuth (auth).
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
- Backblaze B2 account (for storage)

### Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

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
# Run tests using pytest
source .venv/bin/activate
pytest tests/
```

## Directory Structure
- `app/`: Main application code.
    - `api/`: FastAPI routes (`auth`, `intentions`, `jobs`, `me`, `upload`) and dependencies (`dependencies/services.py`).
    - `core/`: Core configurations (database, logging via JSON, queue, security using pydantic-settings).
    - `domain/`: Data models (SQLAlchemy) and schemas (Pydantic), plus interface-like Repositories.
    - `services/`: Business logic services (Auth, EPUB generation, jobs, intentions, upload, etc.).
- `docs/`: Project documentation (architecture, API contract, data model).
- `scripts/`: Maintenance and migration scripts.
- `tests/`: Project tests with unit tests and repository mocks.

## Development Conventions
- **Clean Architecture & Repository Pattern:** Keep business logic strictly in `app/services`. Database logic MUST be handled in `app/domain/repositories`. API routes must only act as IO controllers.
- **Dependency Injection:** Inject repositories and external clients into services. Inject services into routes via `app/api/dependencies/services.py`.
- **Async Processing:** Use `arq` for long-running tasks. Trigger them from `QueueService` and process them in `app/worker.py`.
- **Validation:** Use Pydantic v2 for request/response validation, schemas, and environment configuration (`app/core/config.py`).
- **Observability:** Use structured JSON logging (`app/core/logging.py`) and Sentry for error tracking.
- **Testing:** TDD mindset. Add tests in the `tests/` directory for any new logic. Use `unittest.mock.Mock` to isolate services from their repository dependencies.
