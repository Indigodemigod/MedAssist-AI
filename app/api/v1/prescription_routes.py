import os
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.prescription_repository import PrescriptionRepository
from app.schema.prescription_schema import PrescriptionResponse
from app.services.ocr_service import extract_text_from_image
from app.services.llm_service import (
    extract_medicines_from_text,
    enrich_medicine_info
)

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@router.post("/", response_model=PrescriptionResponse)
def upload_prescription(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        # OCR
        extracted_text = extract_text_from_image(file_path)

        # Medicine Extraction
        medicines = extract_medicines_from_text(extracted_text)

        # Enrichment
        enriched_medicines = []
        for med in medicines:
            details = enrich_medicine_info(med["medicine_name"])
            med.update(details)
            enriched_medicines.append(med)
        print("Enriched Medicines: ", enriched_medicines)
        # Save to DB
        prescription = PrescriptionRepository.create_prescription(
            db=db,
            user_id=user_id,
            image_path=file_path,
            extracted_text=extracted_text,
            analysis_result=enriched_medicines
        )

        return prescription

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
