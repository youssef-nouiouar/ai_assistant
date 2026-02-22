# ============================================================================
# FICHIER : backend/app/api/v1/upload.py
# DESCRIPTION : Endpoint for file/image uploads with OCR text extraction
# ============================================================================

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logger import structured_logger

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    "image/bmp",
}

MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


def _ensure_upload_dir() -> Path:
    """Create the upload directory if it does not exist."""
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


async def _extract_text_from_image(file_path: str) -> str:
    """
    Extract text from an image using OpenAI GPT-4 Vision (or compatible).

    Falls back to an empty string if extraction fails so that the upload
    itself is not blocked.
    """
    import base64

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )

        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        ext = file_path.rsplit(".", 1)[-1].lower()
        mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"

        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract ALL visible text from this screenshot. "
                                "Include error messages, dialog boxes, status bars, "
                                "and any other readable text. Return only the raw "
                                "extracted text, no commentary."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1024,
        )

        extracted = response.choices[0].message.content or ""
        structured_logger.log_info(
            "OCR_EXTRACTION",
            f"Extracted {len(extracted)} chars from {file_path}",
        )
        return extracted.strip()

    except Exception as e:
        structured_logger.log_error("OCR_EXTRACTION_ERROR", str(e))
        return ""


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image attachment (screenshot, photo, etc.).

    Returns the stored file URL and any text extracted via OCR/Vision
    so the frontend can append it to the user's message before analysis.
    """
    # --- Validate MIME type --------------------------------------------------
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non supporté : {file.content_type}. "
            f"Types acceptés : {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    # --- Read & validate size ------------------------------------------------
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier trop volumineux ({len(contents) / 1024 / 1024:.1f} Mo). "
            f"Maximum : {settings.MAX_UPLOAD_MB} Mo.",
        )

    # --- Save to disk --------------------------------------------------------
    upload_dir = _ensure_upload_dir()
    ext = (file.filename or "image.png").rsplit(".", 1)[-1].lower()
    if ext not in ("png", "jpg", "jpeg", "gif", "webp", "bmp"):
        ext = "png"
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = upload_dir / unique_name

    with open(file_path, "wb") as f:
        f.write(contents)

    structured_logger.log_info(
        "FILE_UPLOADED",
        f"{file.filename} -> {unique_name} ({len(contents)} bytes)",
    )

    # --- OCR / Vision text extraction ----------------------------------------
    extracted_text = await _extract_text_from_image(str(file_path))

    # --- Build public URL (served by FastAPI static files or reverse proxy) ---
    file_url = f"/uploads/{unique_name}"

    return {
        "file_url": file_url,
        "file_name": file.filename,
        "extracted_text": extracted_text,
    }
