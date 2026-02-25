from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schema.user_schema import UserCreate, UserResponse, UserSummaryResponse
from app.repositories.user_repository import UserRepository
from app.services.user_summary_service import UserSummaryService
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return UserRepository.create_user(db, user.email, user.full_name)

@router.get("/summary", response_model=UserSummaryResponse)
def get_user_summary(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    summary = UserSummaryService.get_summary(db, current_user.id)
    if not summary:
        raise HTTPException(status_code=404, detail="User summary not found")
    return summary
