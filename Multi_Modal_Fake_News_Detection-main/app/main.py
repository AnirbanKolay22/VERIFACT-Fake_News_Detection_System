import shutil
import socket
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Make project-root imports work for both:
# 1) python app/main.py
# 2) uvicorn app.main:app --reload
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.pipeline import process_request
from utils.scrap_text_from_link import fetch_article_text

app = FastAPI(title="Multimodal Fake News Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend files from the app/ directory regardless of current working directory.
app.mount("/ui", StaticFiles(directory=str(BASE_DIR), html=True), name="frontend")

UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def error_response(message: str) -> dict:
    return {
        "claim": "",
        "verdict": "Error",
        "confidence": 0.0,
        "explanation": message,
    }


def save_upload_file(upload: UploadFile) -> str:
    original_name = Path(upload.filename or "upload.bin").name
    suffix = Path(original_name).suffix
    safe_filename = f"{uuid.uuid4().hex}{suffix}"
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return str(file_path)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/ui")


@app.post("/analyze/link")
async def analyze_link(url: str = Form(...)):
    scraped_text = fetch_article_text(url)
    if scraped_text is None or not scraped_text.strip():
        return error_response("Failed to scrape text from URL")

    payload = {
        "type": "text",
        "input": scraped_text,
    }
    return process_request(payload)


@app.post("/analyze/text")
async def analyze_text(text: str = Form(...)):
    payload = {
        "type": "text",
        "input": text,
    }
    return process_request(payload)


@app.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        file_path = save_upload_file(file)
        payload = {
            "type": "image",
            "input": file_path,
        }
        return process_request(payload)
    except Exception as exc:
        return error_response(f"Image analysis failed: {exc}")


@app.post("/analyze/video")
async def analyze_video(file: UploadFile = File(...)):
    try:
        file_path = save_upload_file(file)
        payload = {
            "type": "video",
            "input": file_path,
        }
        return process_request(payload)
    except Exception as exc:
        return error_response(f"Video analysis failed: {exc}")


if __name__ == "__main__":
    import uvicorn

    host = "127.0.0.1"
    start_port = 8000
    port = start_port

    # Auto-select a free port if 8000 is already in use.
    while port < start_port + 20:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) != 0:
                break
        port += 1

    if port >= start_port + 20:
        raise RuntimeError("No free port found between 8000 and 8019.")

    print(f"Starting server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=False)
