from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.domain.models.user import User
import os
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
JWT_SECRET = os.getenv("JWT_SECRET")

def get_user_from_token(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).get(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return get_user_from_token(token, db)