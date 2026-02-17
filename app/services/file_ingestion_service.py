import os
import mimetypes
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
from app.services.ocr_service import extract_text_from_image
import logging

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/pdf"
]

MAX_FILE_SIZE_MB = 10


class FileIngestionService:

    @staticmethod
    def validate_file(file):
        content_type = file.content_type

        if content_type not in SUPPORTED_TYPES:
            raise ValueError("Unsupported file type.")

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError("File size exceeds 10MB limit.")

        return content_type

    @staticmethod
    def extract_text(file_path: str, content_type: str):

        if content_type.startswith("image"):
            logger.info("Processing image file via OCR.")
            text = extract_text_from_image(file_path)
            return text

        elif content_type == "application/pdf":
            logger.info("Processing PDF file.")

            # First attempt: direct text extraction
            text = FileIngestionService._extract_text_from_pdf(file_path)

            if text.strip():
                logger.info("Text-based PDF detected.")
                return text

            logger.info("Scanned PDF detected. Converting to images.")
            return FileIngestionService._ocr_scanned_pdf(file_path)

        else:
            raise ValueError("Unsupported file format.")

    @staticmethod
    def _extract_text_from_pdf(file_path: str):
        text_content = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text_content += page.extract_text() or ""

        return text_content

    @staticmethod
    def _ocr_scanned_pdf(file_path: str):
        doc = fitz.open(file_path)
        full_text = ""

        for page_number in range(len(doc)):
            page = doc[page_number]
            pix = page.get_pixmap()
            image_path = f"temp_page_{page_number}.png"
            pix.save(image_path)

            text = extract_text_from_image(image_path)
            full_text += text

            os.remove(image_path)

        return full_text
