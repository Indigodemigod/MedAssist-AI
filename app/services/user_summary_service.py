from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.prescription import Prescription
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.user import User
import os
import json

class UserSummaryService:

    @staticmethod
    def get_summary(db: Session, user_id: int):
        # 1. Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # 2. Get prescriptions
        prescriptions = db.query(Prescription).filter(Prescription.user_id == user_id).all()
        total_prescriptions = len(prescriptions)

        # 3. Calculate total medicines
        total_medicines = 0
        for p in prescriptions:
            if p.analysis_result:
                # Handle both string and list
                analysis = p.analysis_result
                if isinstance(analysis, str):
                    try:
                        analysis = json.loads(analysis)
                    except:
                        analysis = []
                
                if isinstance(analysis, list):
                    total_medicines += len(analysis)

        # 4. Calculate total questions asked (messages where role == 'user')
        # We need to join Prescription -> ChatSession -> ChatMessage
        total_questions = db.query(func.count(ChatMessage.id)).\
            join(ChatSession, ChatMessage.session_id == ChatSession.id).\
            join(Prescription, ChatSession.prescription_id == Prescription.id).\
            filter(Prescription.user_id == user_id).\
            filter(ChatMessage.role == 'user').scalar()

        # 5. Last prescription info
        last_prescription = db.query(Prescription).\
            filter(Prescription.user_id == user_id).\
            order_by(Prescription.created_at.desc()).\
            first()

        last_prescription_upload_time = None
        last_prescription_name = None

        if last_prescription:
            last_prescription_upload_time = last_prescription.created_at
            if last_prescription.image_path:
                last_prescription_name = os.path.basename(last_prescription.image_path)

        return {
            "full_name": user.full_name,
            "total_prescriptions": total_prescriptions,
            "total_medicines": total_medicines,
            "total_questions": total_questions or 0,
            "last_prescription_upload_time": last_prescription_upload_time,
            "last_prescription_name": last_prescription_name
        }
