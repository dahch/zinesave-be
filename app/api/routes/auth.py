import os

from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
from fastapi.exceptions import HTTPException
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse

from app.domain.schemas.auth import Register, Login
from app.domain.models.user import User

from app.api.dependencies.database import get_db
from app.core.security import create_access_token
from app.core.password import hash_password, verify_password
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.auth import get_user_from_token
from app.domain.models.cloud_connection import CloudConnection
import requests as requests_lib

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
router = APIRouter(prefix="/auth", tags=["Auth"])

def resolve_user(db: Session, google_info: dict) -> User:
    user = (
        db.query(User)
        .filter(
            User.provider == "google",
            User.provider_id == google_info["sub"]
        )
        .first()
    )

    if user:
        return user
    
    #fallback by email
    user = db.query(User).filter(User.email == google_info["email"]).first()

    if user and user.provider == "email":
        user.provider = "google"
        user.provider_id = google_info["sub"]
        db.commit()
        return user

    if (user):
        user.provider = "google"
        user.provider_id = google_info["sub"]
        db.commit()
        return user

    user = User(
        email=google_info["email"],
        name=google_info.get("name"),
        provider="google",
        provider_id=google_info["sub"],
        plan="free"
    )
    db.add(user)
    db.commit()
    return user

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

@router.get("/google")
def google_login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/google/callback"
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )

    return {"auth_url": auth_url}

@router.get("/google/authorize")
def google_authorize(user: User = Depends(get_current_user)):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/google/callback"
    )

    state = create_access_token(user)
    
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state
    )

    return {"auth_url": auth_url}

@router.get("/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    state = request.query_params.get("state")
    existing_user = None

    if state:
        try:
            # Attempt to decode state as user token (Binding Flow)
            # We catch exception because normal login might have a state (if used) or invalid one
            existing_user = get_user_from_token(state, db)
        except Exception:
            existing_user = None

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/google/callback",
        state=state 
    )

    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials

    # print(os.getenv("GOOGLE_CLIENT_ID"))
    transport = requests.Request()
    idinfo = id_token.verify_oauth2_token(
        creds.id_token,
        transport,
        os.getenv("GOOGLE_CLIENT_ID")
    )
    
    target_user = None
    is_binding = False

    if existing_user:
        # Binding to existing authenticated user
        target_user = existing_user
        is_binding = True
    else:
        # Login/Register flow
        target_user = resolve_user(db, idinfo)
        is_binding = False

    # Update Cloud Connection
    # Check if connection exists
    connection = (
        db.query(CloudConnection)
        .filter(
            CloudConnection.user_id == target_user.id,
            CloudConnection.provider == "google_drive"
        )
        .first()
    )

    if not connection:
        connection = CloudConnection(
            user_id=target_user.id,
            provider="google_drive"
        )
        db.add(connection)
    
    connection.access_token = creds.token
    connection.refresh_token = creds.refresh_token
    if creds.expiry:
        connection.expires_at = creds.expiry

    connection.metadata_info = {"email": idinfo.get("email")}

    db.commit()

    frontend_url = os.getenv("FRONTEND_URL")

    if is_binding:
        # Redirect to account page
        return RedirectResponse(url=f"{frontend_url}/dashboard/account")
    else:
        # Redirect with login token
        token = create_access_token(target_user)
        return RedirectResponse(url=f"{frontend_url}/auth/callback?token={token}")

@router.post("/register")
def register(data: Register, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already exists")

    user = User(
        email=data.email,
        name=data.name,
        provider="email",
        provider_id=data.email,
        password_hash=hash_password(data.password),
        plan="free",
        is_company=data.is_company,
        country=data.country,
        vat_number=data.vat_number
    )

    db.add(user)
    db.commit()

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/login")
def login(data: Login, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            User.email == data.email,
            User.provider == "email"
        )
        .first()
    )

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# --- DROPBOX AUTH ---
@router.get("/dropbox/authorize")
def dropbox_authorize(user: User = Depends(get_current_user)):
    client_id = os.getenv("DROPBOX_CLIENT_ID")
    redirect_uri = "http://localhost:8000/auth/dropbox/callback"
    
    # Create short-lived token for state
    state = create_access_token(user)
    
    url = f"https://www.dropbox.com/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&token_access_type=offline&state={state}"
    return {"auth_url": url}

@router.get("/dropbox/callback")
def dropbox_callback(code: str, state: str, db: Session = Depends(get_db)):
    # Verify State
    user = get_user_from_token(state, db)

    client_id = os.getenv("DROPBOX_CLIENT_ID")
    client_secret = os.getenv("DROPBOX_CLIENT_SECRET")
    redirect_uri = "http://localhost:8000/auth/dropbox/callback"
    
    # Exchange code for token
    token_url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
    
    response = requests_lib.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(400, "Failed to get Dropbox token")
        
    tokens = response.json()
    
    # Save Connection
    connection = db.query(CloudConnection).filter(
        CloudConnection.user_id == user.id,
        CloudConnection.provider == "dropbox"
    ).first()
    
    if not connection:
        connection = CloudConnection(user_id=user.id, provider="dropbox")
        db.add(connection)
        
    connection.access_token = tokens["access_token"]
    connection.refresh_token = tokens.get("refresh_token") # Only allowed if token_access_type=offline
    
    db.commit()
    
    # Redirect to Frontend
    frontend_url = os.getenv("FRONTEND_URL")
    return RedirectResponse(url=f"{frontend_url}/dashboard/account")

# --- ONEDRIVE AUTH ---
@router.get("/onedrive/authorize")
def onedrive_authorize(user: User = Depends(get_current_user)):
    client_id = os.getenv("ONEDRIVE_CLIENT_ID")
    redirect_uri = "http://localhost:8000/auth/onedrive/callback"
    scope = "Files.ReadWrite User.Read offline_access"
    
    # State with user token
    state = create_access_token(user)
    
    url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={client_id}&response_type=code&redirect_uri={redirect_uri}"
        f"&response_mode=query&scope={scope}&state={state}"
    )
    return {"auth_url": url}

@router.get("/onedrive/callback")
def onedrive_callback(code: str, state: str, db: Session = Depends(get_db)):
    # Verify State
    user = get_user_from_token(state, db)

    client_id = os.getenv("ONEDRIVE_CLIENT_ID")
    client_secret = os.getenv("ONEDRIVE_CLIENT_SECRET")
    redirect_uri = "http://localhost:8000/auth/onedrive/callback"
    
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "scope": "Files.ReadWrite User.Read offline_access",
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "client_secret": client_secret
    }
    
    response = requests_lib.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(400, f"Failed to get OneDrive token: {response.text}")
        
    tokens = response.json()
    
    connection = db.query(CloudConnection).filter(
        CloudConnection.user_id == user.id,
        CloudConnection.provider == "onedrive"
    ).first()
    
    if not connection:
        connection = CloudConnection(user_id=user.id, provider="onedrive")
        db.add(connection)
        
    connection.access_token = tokens["access_token"]
    connection.refresh_token = tokens.get("refresh_token")
    
    db.commit()
    
    frontend_url = os.getenv("FRONTEND_URL")
    return RedirectResponse(url=f"{frontend_url}/dashboard/account")