import pytest
from unittest.mock import patch
from datetime import datetime
from app.domain.models.user import User
from app.domain.models.job import Job
from app.main import app
from app.api.dependencies.auth import get_current_user

def test_create_job(client, user_repo, job_repo):
    user = User(id="1", email="test@example.com", credits=10)
    app.dependency_overrides[get_current_user] = lambda: user
    
    job_repo.get_recent_duplicate.return_value = None
    job_repo.add.return_value = Job(
        id="123", source_url="https://example.com", user_id="1", 
        status="pending", progress=0, created_at=datetime.utcnow(), external_uploads={}
    )
    
    with patch("app.services.job_service.socket.getaddrinfo") as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("93.184.216.34", 0))]
        response = client.post("/jobs", json={"url": "https://example.com"})
        
    assert response.status_code == 202
    assert response.json()["source_url"] == "https://example.com"

def test_get_jobs(client, user_repo, job_repo):
    user = User(id="1", email="test@example.com", credits=10)
    app.dependency_overrides[get_current_user] = lambda: user
    
    mock_job = Job(
        id="123", source_url="https://example.com", user_id="1", 
        status="pending", progress=0, created_at=datetime.utcnow(), external_uploads={}
    )
    job_repo.get_user_jobs_paginated.return_value = ([mock_job], 1)
    
    response = client.get("/jobs?page=1&per_page=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["jobs"]) == 1
