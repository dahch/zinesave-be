from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

JWT_SECRET = settings.JWT_SECRET
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is not set. "
        "This is required for authentication security. "
        "Set it to a strong random string in your .env file."
    )

JWT_EXP_MINUTES = 60

def create_access_token(user):
    payload = {
        "sub": user.id,
        "email": user.email,
        "plan":  user.plan,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXP_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

RESET_TOKEN_EXP_MINUTES = 15

def create_reset_token(email: str) -> str:
    payload = {
        "sub": email,
        "type": "reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXP_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_reset_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "reset":
            return None
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
