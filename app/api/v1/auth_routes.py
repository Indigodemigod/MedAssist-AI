from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schema.auth_schema import RegisterRequest, LoginRequest, TokenResponse
from app.services import auth_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_user(db, req.email, req.full_name, req.password)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    token = auth_service.create_access_token({"user_id": user.id})
    logger.info(f"User registered: {user.email}")
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user_with_password(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth_service.create_access_token({"user_id": user.id})
    logger.info(f"User login: {user.email}")
    return TokenResponse(access_token=token)
