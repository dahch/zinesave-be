import logging
import os

import requests as requests_lib
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, get_user_from_token
from app.api.dependencies.database import get_db
from app.api.dependencies.services import get_auth_service
from app.core.config import settings
from app.core.security import create_access_token
from app.domain.models.user import User
from app.domain.schemas.auth import ForgotPassword, Login, Register, ResetPassword
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

if settings.ENVIRONMENT != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_google_client_config():
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "project_id": settings.GOOGLE_PROJECT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [
                settings.BACKEND_URL + "/auth/google/callback",
                "http://localhost:8000/auth/google/callback",
            ],
        }
    }


SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


@router.get("/google")
def google_login():
    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.BACKEND_URL + "/auth/google/callback",
    )

    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

    return {"auth_url": auth_url}


@router.get("/google/authorize")
def google_authorize(user: User = Depends(get_current_user)):
    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.BACKEND_URL + "/auth/google/callback",
    )

    state = create_access_token(user)

    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent", state=state)

    return {"auth_url": auth_url}


@router.get("/google/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    state = request.query_params.get("state")
    existing_user = None

    if state:
        try:
            existing_user = get_user_from_token(state, db)
        except Exception:
            existing_user = None

    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.BACKEND_URL + "/auth/google/callback",
        state=state,
    )

    code = request.query_params.get("code")
    token_response = flow.fetch_token(code=code)
    creds = flow.credentials
    transport = google_requests.Request()
    idinfo = id_token.verify_oauth2_token(creds.id_token, transport, settings.GOOGLE_CLIENT_ID)

    target_user = None
    is_binding = False

    if existing_user:
        target_user = existing_user
        is_binding = True
    else:
        target_user = auth_service.resolve_oauth_user(
            email=idinfo.get("email"),
            name=idinfo.get("name"),
            provider_id=idinfo.get("sub"),
            provider="google",
        )
        is_binding = False

    granted_scopes = token_response.get("scope", "")
    drive_scope = "https://www.googleapis.com/auth/drive.file"

    if drive_scope in granted_scopes:
        auth_service.save_cloud_connection(
            user_id=target_user.id,
            provider="google_drive",
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            expiry=creds.expiry,
            metadata={"email": idinfo.get("email")},
        )

    frontend_url = settings.FRONTEND_URL

    if is_binding:
        return RedirectResponse(url=f"{frontend_url}/dashboard/account")
    else:
        token = create_access_token(target_user)
        return RedirectResponse(url=f"{frontend_url}/auth/callback?token={token}")


limiter = Limiter(key_func=get_remote_address)


@router.post("/register")
@limiter.limit("5/minute")
def register(
    request: Request, data: Register, auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.register_user(data)
    return {"message": "Registration successful. Please check your email to verify your account."}


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, data: Login, auth_service: AuthService = Depends(get_auth_service)):
    token = auth_service.login_user(data)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/verify")
def verify_email(
    token: str, db: Session = Depends(get_db), auth_service: AuthService = Depends(get_auth_service)
):
    user = get_user_from_token(token, db)
    new_token = auth_service.verify_email(user)
    return {
        "message": "Email verified successfully",
        "access_token": new_token,
        "token_type": "bearer",
    }


@router.post("/resend-verification")
@limiter.limit("3/minute")
def resend_verification(
    request: Request, email: str, auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.resend_verification(email)
    return {
        "message": "If the email is registered and not yet verified, a verification link has been sent."
    }


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request, data: ForgotPassword, auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.request_password_reset(data.email)
    return {"message": "If the email is registered, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPassword, auth_service: AuthService = Depends(get_auth_service)):
    auth_service.reset_password(data)
    return {"message": "Password updated successfully"}


# --- DROPBOX AUTH ---
@router.get("/dropbox/authorize")
def dropbox_authorize(user: User = Depends(get_current_user)):
    client_id = settings.DROPBOX_CLIENT_ID
    redirect_uri = settings.BACKEND_URL + "/auth/dropbox/callback"
    state = create_access_token(user)
    url = f"https://www.dropbox.com/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&token_access_type=offline&state={state}"
    return {"auth_url": url}


@router.get("/dropbox/callback")
def dropbox_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = get_user_from_token(state, db)

    client_id = settings.DROPBOX_CLIENT_ID
    client_secret = settings.DROPBOX_CLIENT_SECRET
    redirect_uri = settings.BACKEND_URL + "/auth/dropbox/callback"

    token_url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }

    response = requests_lib.post(token_url, data=data)
    tokens = response.json()

    auth_service.save_cloud_connection(
        user_id=user.id,
        provider="dropbox",
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
    )

    frontend_url = settings.FRONTEND_URL
    return RedirectResponse(url=f"{frontend_url}/dashboard/account")


# --- ONEDRIVE AUTH ---
@router.get("/onedrive/authorize")
def onedrive_authorize(user: User = Depends(get_current_user)):
    client_id = settings.ONEDRIVE_CLIENT_ID
    redirect_uri = settings.BACKEND_URL + "/auth/onedrive/callback"
    scope = "Files.ReadWrite User.Read offline_access"
    state = create_access_token(user)

    url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={client_id}&response_type=code&redirect_uri={redirect_uri}"
        f"&response_mode=query&scope={scope}&state={state}"
    )
    return {"auth_url": url}


@router.get("/onedrive/callback")
def onedrive_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = get_user_from_token(state, db)

    client_id = settings.ONEDRIVE_CLIENT_ID
    client_secret = settings.ONEDRIVE_CLIENT_SECRET
    redirect_uri = settings.BACKEND_URL + "/auth/onedrive/callback"

    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "scope": "Files.ReadWrite User.Read offline_access",
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "client_secret": client_secret,
    }

    response = requests_lib.post(token_url, data=data)
    tokens = response.json()

    auth_service.save_cloud_connection(
        user_id=user.id,
        provider="onedrive",
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
    )

    frontend_url = settings.FRONTEND_URL
    return RedirectResponse(url=f"{frontend_url}/dashboard/account")
