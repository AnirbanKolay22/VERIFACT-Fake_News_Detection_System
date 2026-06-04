import os
import re

import cv2
import pytesseract

from src.claim_from_text import summarize_text

DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Allow explicit override with environment variable.
if os.getenv("TESSERACT_CMD"):
    pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")
elif os.path.exists(DEFAULT_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_PATH


def extract_text_from_image(image_path: str) -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Image not found or unreadable.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    try:
        text = pytesseract.image_to_string(gray, lang="eng")
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed. Install Tesseract and add it to PATH "
            "or set the TESSERACT_CMD environment variable."
        ) from exc

    return text.strip()


def is_text_image(text: str) -> bool:
    if not text:
        return False

    clean = re.sub(r"[^A-Za-z ]", "", text)
    words = clean.split()

    if len(clean) < 40:
        return False
    if len(words) < 6:
        return False

    return True


def non_text_fallback_summary() -> str:
    return (
        "The provided image does not contain enough readable text to extract a "
        "reliable factual claim for verification."
    )


def image_to_text_summary(image_path: str) -> dict:
    try:
        text = extract_text_from_image(image_path)
    except Exception as exc:
        return {
            "status": "error",
            "summary": str(exc),
        }

    if is_text_image(text):
        summary = summarize_text(text)
        status = "text_image"
    else:
        summary = non_text_fallback_summary()
        status = "non_text_image"

    return {
        "status": status,
        "summary": summary,
    }


if __name__ == "__main__":
    print(image_to_text_summary("data/image/news2.jpg"))
