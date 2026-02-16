import easyocr
import logging
logger = logging.getLogger(__name__)

reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_image(image_path: str) -> str:
    try:
        logger.info(f"Starting OCR for image: {image_path}")
        results = reader.readtext(image_path, detail=0, paragraph=True)
        extracted_text = " ".join(results)
        logger.info(f"OCR completed. Extracted length: {len(extracted_text)} characters")
        return extracted_text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"
