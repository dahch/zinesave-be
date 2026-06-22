import pytest
from app.domain.models.user import User
from app.core.password import hash_password

def test_register_success(client, user_repo):
    user_repo.get_by_email.return_value = None
    
    response = client.post("/auth/register", json={
        "email": "new@example.com",
        "name": "New User",
        "password": "Password123!",
        "is_company": False
    })
    
    assert response.status_code == 200
    assert "message" in response.json()

def test_login_success(client, user_repo):
    hashed = hash_password("Password123!")
    user_repo.get_by_email.return_value = User(
        id="1", email="test@example.com", provider="email", password_hash=hashed, is_verified=True, is_active=True
    )
    
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "Password123!"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials(client, user_repo):
    user_repo.get_by_email.return_value = None
    
    response = client.post("/auth/login", json={
        "email": "wrong@example.com",
        "password": "Password123!"
    })
    
    assert response.status_code == 401
from app.api.dependencies.auth import get_current_user
from app.main import app

def test_google_login(client):
    response = client.get("/auth/google")
    assert response.status_code == 200
    assert "auth_url" in response.json()

def test_google_authorize(client):
    user = User(id="1", email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: user
    response = client.get("/auth/google/authorize")
    assert response.status_code == 200
    assert "auth_url" in response.json()

def test_dropbox_authorize(client):
    user = User(id="1", email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: user
    response = client.get("/auth/dropbox/authorize")
    assert response.status_code == 200
    assert "auth_url" in response.json()

def test_onedrive_authorize(client):
    user = User(id="1", email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: user
    response = client.get("/auth/onedrive/authorize")
    assert response.status_code == 200
    assert "auth_url" in response.json()
