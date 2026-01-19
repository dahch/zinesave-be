FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for some python packages like lxml, pillow)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables should be passed via docker-compose
# But we can set defaults here if needed
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
