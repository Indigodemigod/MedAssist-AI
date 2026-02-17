import re
from rapidfuzz import fuzz
from typing import List, Dict, Any


ORDINAL_MAP = {
    "first": 0,
    "1st": 0,
    "second": 1,
    "2nd": 1,
    "third": 2,
    "3rd": 2,
    "fourth": 3,
    "4th": 3,
}


GLOBAL_MEDICINE_KEYWORDS = [
    "all medicines",
    "each medicine",
    "these medicines",
    "every medicine",
    "all of them",
    "all about",
    "tell me about each",
    "tell me about all"
]


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.strip()


def clean_medicine_name(name: str) -> str:
    name = normalize_text(name)
    name = re.sub(r"\b(tab|tablet|cap|capsule|inj|injection)\b", "", name)
    return name.strip()


class MedicineMatcher:

    @staticmethod
    def detect(question: str, medicines: List[Dict[str, Any]]) -> Dict[str, Any]:

        normalized_question = normalize_text(question)

        # 1️⃣ Global "all medicines" detection
        for keyword in GLOBAL_MEDICINE_KEYWORDS:
            if keyword in normalized_question:
                return {
                    "type": "all",
                    "medicines": medicines
                }

        # 2️⃣ Index-based detection
        for word, idx in ORDINAL_MAP.items():
            if word in normalized_question and idx < len(medicines):
                return {
                    "type": "index",
                    "medicines": [medicines[idx]]
                }

        # 3️⃣ Fuzzy name detection (multiple supported)
        matches = []

        for med in medicines:
            med_name_clean = clean_medicine_name(med.get("medicine_name", ""))

            score = fuzz.partial_ratio(
                med_name_clean,
                normalized_question
            )

            if score >= 75:
                matches.append((score, med))

        if matches:
            matches.sort(key=lambda x: x[0], reverse=True)
            detected = [m[1] for m in matches]

            return {
                "type": "name",
                "medicines": detected
            }

        return {
            "type": None,
            "medicines": []
        }
