from datetime import datetime, timedelta
import jwt
import os

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_EXP_MINUTES = 60

def create_access_token(user):
    payload = {
        "sub": user.id,
        "email": user.email,
        "plan":  user.plan,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
