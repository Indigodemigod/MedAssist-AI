from sqlalchemy.orm import Session
from app.models.prescription import Prescription

class PrescriptionRepository:

    @staticmethod
    def create_prescription(
        db: Session,
        user_id: int,
        image_path: str,
        extracted_text: str = "",
        analysis_result=None
    ):
        if analysis_result is None:
            analysis_result = []
        prescription = Prescription(
            user_id=user_id,
            image_path=image_path,
            extracted_text=extracted_text,
            analysis_result=analysis_result
        )
        db.add(prescription)
        db.commit()
        db.refresh(prescription)
        return prescription

    @staticmethod
    def get_prescriptions_by_user(db: Session, user_id: int):
        return db.query(Prescription).filter(
            Prescription.user_id == user_id
        ).all()
