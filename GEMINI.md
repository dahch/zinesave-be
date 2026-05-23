# GEMINI.md - Reader to EPUB Converter

## Project Overview
This project is a FastAPI-based API designed to convert reader content (articles, URLs, etc.) into EPUB format. It features a background processing system for handling conversions asynchronously and integrates with cloud storage for file management.

- **Primary Technologies:** Python 3.12, FastAPI, SQLAlchemy (PostgreSQL), Redis (arq), Backblaze B2 (boto3).
- **Secondary Technologies:** Sentry (monitoring), MailerSend (emails), Google OAuth (auth).
- **Architecture:** Clean Architecture principles with separation into API routes, services for business logic, and domain models for data representation. Background tasks are handled by `arq`.

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
pytest
```

## Directory Structure
- `app/`: Main application code.
    - `api/`: FastAPI routes (`auth`, `jobs`, `me`, `upload`) and dependencies.
    - `core/`: Core configurations (database, logging, queue, security).
    - `domain/`: Data models (SQLAlchemy) and schemas (Pydantic).
    - `services/`: Business logic services (EPUB generation, extraction, normalization, storage, etc.).
- `docs/`: Project documentation (architecture, API contract, data model).
- `scripts/`: Maintenance and migration scripts.
- `tests/`: Project tests.

## Development Conventions
- **Clean Architecture:** Keep business logic in `app/services` and data structures in `app/domain`.
- **Async Processing:** Use `arq` for long-running tasks. Trigger them from the API and process them in `app/worker.py`.
- **Validation:** Use Pydantic v2 for request/response validation and schemas.
- **Error Handling:** Use Sentry for error reporting. Wrap background tasks in proper error handling to update job status in the database.
- **Environment Variables:** All configuration should be managed via `.env` and accessed through `app/core/config.py`.
- **Testing:** Add tests in the `tests/` directory for new features or bug fixes.
