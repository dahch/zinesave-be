import pytest
from unittest.mock import patch, Mock
from app.services.email_service import EmailService
from app.services.email_templates import create_verification_email, create_reset_password_email

@patch("app.services.email_service.MailerSendClient")
def test_send_verification_email(mock_client):
    service = EmailService()
    mock_instance = mock_client.return_value
    service.client = mock_instance
    service.send_verification_email("test@example.com", "http://verify")
    mock_instance.emails.send.assert_called_once()

@patch("app.services.email_service.MailerSendClient")
def test_send_password_reset_email(mock_client):
    service = EmailService()
    mock_instance = mock_client.return_value
    service.client = mock_instance
    service.send_password_reset_email("test@example.com", "http://reset")
    mock_instance.emails.send.assert_called_once()

def test_email_templates():
    assert "verify" in create_verification_email("http://verify", "http://frontend")
    assert "reset" in create_reset_password_email("http://reset", "http://frontend")
