import logging

from mailersend import EmailContact, EmailRequest, MailerSendClient

from app.core.config import settings
from app.services.email_templates import (
    create_reset_password_email,
    create_verification_email,
    create_welcome_email,
)

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.api_key = settings.MAILERSEND_API_KEY
        self.from_email = settings.MAILERSEND_FROM_EMAIL
        self.frontend_url = settings.FRONTEND_URL

        if not self.api_key:
            logger.warning("MAILERSEND_API_KEY not set — email sending will fail")

        self.client = MailerSendClient(api_key=self.api_key)

    def send_verification_email(self, to_email: str, verification_link: str):
        email_body = create_verification_email(verification_link, self.frontend_url)

        text_body = f"Welcome to ZineSave! Please verify your email by copying this link: {verification_link}"

        try:
            req = EmailRequest(
                from_email=EmailContact(email=self.from_email, name="ZineSave"),
                to=[EmailContact(email=to_email)],
                subject="Verify your email for ZineSave",
                html=email_body,
                text=text_body,
            )

            response = self.client.emails.send(req)
            return response
        except Exception as e:
            logger.error(f"Error sending verification email to {to_email}: {e}")
            return None

    def send_password_reset_email(self, to_email: str, reset_link: str):
        email_body = create_reset_password_email(reset_link, self.frontend_url)
        text_body = f"Reset your password by copying this link: {reset_link}"

        try:
            req = EmailRequest(
                from_email=EmailContact(email=self.from_email, name="ZineSave"),
                to=[EmailContact(email=to_email)],
                subject="Reset your password for ZineSave",
                html=email_body,
                text=text_body,
            )

            response = self.client.emails.send(req)
            return response
        except Exception as e:
            logger.error(f"Error sending password reset email to {to_email}: {e}")
            return None

    def send_welcome_email(self, to_email: str):
        email_body = create_welcome_email(self.frontend_url, settings.CONTACT_EMAIL)
        text_body = f"Welcome to ZineSave! We're thrilled to have you on board. If you have any questions, reach out to us at {settings.CONTACT_EMAIL}."

        try:
            req = EmailRequest(
                from_email=EmailContact(email=self.from_email, name="ZineSave"),
                to=[EmailContact(email=to_email)],
                subject="Welcome to ZineSave!",
                html=email_body,
                text=text_body,
            )

            response = self.client.emails.send(req)
            return response
        except Exception as e:
            logger.error(f"Error sending welcome email to {to_email}: {e}")
            return None
