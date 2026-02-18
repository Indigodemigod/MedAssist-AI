from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    secret = os.getenv("SECRET_KEY", "devsecret")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query.__self__ if False else None
    user = UserRepository.get_user_by_email(db, "") if False else None
    # fetch by id
    user = db.query(UserRepository.__dict__.get('create_user').__self__ if False else object) if False else None
    # fallback: query User directly
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
