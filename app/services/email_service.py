import os
from mailersend import MailerSendClient
from mailersend import EmailRequest, EmailContact

from app.services.email_templates import create_verification_email

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("MAILERSEND_API_KEY")
        self.from_email = os.getenv("MAILERSEND_FROM_EMAIL", "noreply@zinesave.com")
        self.frontend_url = os.getenv("FRONTEND_URL", "https://zinesave.io")
        
        if not self.api_key:
            print("Warning: MAILERSEND_API_KEY not set")
            # We might want to handle this gracefully or fail hard depending on requirements
            
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
                text=text_body
            )
            
            response = self.client.emails.send(req)
            return response
        except Exception as e:
            print(f"Error sending email: {e}")
            return None
