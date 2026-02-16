from sqlalchemy.orm import Session
from app.models.user import User

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
