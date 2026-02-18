from sqlalchemy.orm import Session
from app.models.user import User
from passlib.context import CryptContext

# Use bcrypt for better Windows compatibility (prebuilt wheels available)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:

    @staticmethod
    def create_user(db: Session, email: str, full_name: str):
        user = User(email=email, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user_with_password(db: Session, email: str, full_name: str, password: str):
        hashed = pwd_context.hash(password)
        user = User(email=email, full_name=full_name, password_hash=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
