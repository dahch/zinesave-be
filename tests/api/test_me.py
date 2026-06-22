import pytest
from datetime import datetime
from app.domain.models.user import User
from app.main import app
from app.api.dependencies.auth import get_current_user

def test_get_me(client, user_repo):
    user = User(
        id="1", email="test@example.com", name="Test User", plan="free", 
        credits=10, is_beta_tester=True, is_active=True, is_company=False, 
        country="US", vat_number=None, created_at=datetime.utcnow()
    )
    app.dependency_overrides[get_current_user] = lambda: user
    
    response = client.get("/me")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["name"] == "Test User"
