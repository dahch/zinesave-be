import pytest
from unittest.mock import MagicMock
from app.domain.models.user import User
from app.domain.schemas.user import UserUpdate

def test_get_me(user_service, cloud_conn_repo):
    user = User(id=1, email="test@example.com")
    
    # Mocking the chain: self.cloud_conn_repo.db.query().filter().all()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_all = MagicMock(return_value=[("google_drive",), ("dropbox",)])
    
    cloud_conn_repo.db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.all = mock_all
    
    result = user_service.get_me(user)
    
    assert result["email"] == "test@example.com"
    assert result["connected_providers"] == ["google_drive", "dropbox"]

def test_update_me(user_service, user_repo):
    user = User(id=1, country="US")
    data = UserUpdate(country="ES", is_company=True, vat_number="12345")
    
    user_repo.update.return_value = user
    
    result = user_service.update_me(user, data)
    
    assert user.country == "ES"
    assert user.is_company is True
    assert user.vat_number == "12345"
    user_repo.update.assert_called_once_with(user)
