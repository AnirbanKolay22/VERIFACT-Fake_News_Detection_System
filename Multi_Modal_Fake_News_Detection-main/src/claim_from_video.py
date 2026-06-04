import json
import os
import re
import shutil
import uuid

import whisper
from moviepy.video.io.VideoFileClip import VideoFileClip

from src.claim_from_text import summarize_text

WHISPER_MODEL_SIZE = "base"
_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    return _whisper_model


def extract_audio_from_video(video_path: str) -> str:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is not available in PATH. Install FFmpeg to process video files.")

    audio_path = f"temp_audio_{uuid.uuid4().hex}.wav"
    clip = VideoFileClip(video_path)

    try:
        if clip.audio is None:
            raise RuntimeError("No audio track found in the uploaded video.")
        clip.audio.write_audiofile(audio_path, logger=None)
    finally:
        clip.close()

    return audio_path


def clean_transcript(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9., ]", "", text)
    return text.strip()


def extract_claim_from_video(video_path: str) -> dict:
    if not os.path.exists(video_path):
        return {
            "status": "failed",
            "reason": "Video file not found.",
        }

    try:
        audio_path = extract_audio_from_video(video_path)
    except Exception as exc:
        return {
            "status": "failed",
            "reason": str(exc),
        }

    raw_transcript = ""
    try:
        transcription = get_whisper_model().transcribe(audio_path)
        raw_transcript = transcription.get("text", "")
    except Exception as exc:
        return {
            "status": "failed",
            "reason": f"Speech-to-text failed: {exc}",
        }
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

    cleaned_transcript = clean_transcript(raw_transcript)

    if len(cleaned_transcript.split()) < 20:
        return {
            "status": "failed",
            "reason": "Insufficient spoken content in video.",
            "raw_transcript": raw_transcript,
        }

    extracted_claim = summarize_text(cleaned_transcript)

    return {
        "status": "success",
        "input_type": "video",
        "extracted_claim": extracted_claim,
        "transcript_snippet": cleaned_transcript[:300],
        "confidence_hint": "medium",
        "ready_for_evidence_search": True,
    }


if __name__ == "__main__":
    video_path = "src/input.mp4"
    result = extract_claim_from_video(video_path)
    print(json.dumps(result, indent=4, ensure_ascii=False))
