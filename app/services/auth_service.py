import os
from datetime import datetime, timedelta
import jwt
from app.repositories.user_repository import UserRepository


def create_access_token(data: dict, expires_hours: int = 24) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    to_encode.update({"exp": expire})
    secret = os.getenv("SECRET_KEY", "devsecret")
    token = jwt.encode(to_encode, secret, algorithm="HS256")
    return token


def register_user(db, email: str, full_name: str, password: str):
    existing = UserRepository.get_user_by_email(db, email)
    if existing:
        raise ValueError("User already exists")
    # Create user and store hashed password
    return UserRepository.create_user_with_password(db, email, full_name, password)


def authenticate_user(db, email: str):
    return UserRepository.get_user_by_email(db, email)


def authenticate_user_with_password(db, email: str, password: str):
    user = UserRepository.get_user_by_email(db, email)
    if not user or not user.password_hash:
        return None
    from app.repositories.user_repository import UserRepository as UR
    if UR.verify_password(password, user.password_hash):
        return user
    return None
