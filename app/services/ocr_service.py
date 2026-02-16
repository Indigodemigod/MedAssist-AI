import easyocr

reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_image(image_path: str) -> str:
    try:
        results = reader.readtext(image_path, detail=0, paragraph=True)
        extracted_text = " ".join(results)
        print("Extracted Text:", extracted_text)
        return extracted_text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"
