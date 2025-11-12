"""
FastAPI backend for Claude-style chatbot interface.
Provides chat and file upload endpoints that integrate with the existing orchestrator.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from orchestrator import create_orchestrator
from tools.pdf_parser import PDFParserTool


logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    file_context: Optional[str] = Field(default=None, max_length=20000)


class ChatResponse(BaseModel):
    response: str
    status: str
    session_id: Optional[str]


def _sanitize_text(text: str) -> str:
    """Basic text sanitisation to strip control characters."""
    clean = text.replace("\x00", "").strip()
    return clean


# FastAPI application setup
app = FastAPI(title="Claude-Style Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

orchestrator = create_orchestrator()
pdf_parser = PDFParserTool()

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
ALLOWED_PDF_TYPES = {"application/pdf"}


@app.get("/api/health")
async def health() -> dict:
    """Health-check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Process chat messages through the orchestrator."""
    message = _sanitize_text(payload.message)
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    logger.info("Processing chat message")

    final_input = message
    if payload.file_context:
        context = _sanitize_text(payload.file_context)
        final_input = f"Context:\n{context}\n\nQuestion:\n{message}"

    try:
        results = orchestrator.process_query(final_input)
    except Exception as exc:  # pragma: no cover - orchestrator internal failure
        logger.error("Error in orchestrator: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to process message.") from exc

    execution_results = results.get("execution_results", [])
    response_text = results.get("final_response")

    if not response_text:
        response_text = "I wasn't able to generate a response. Please try again."

        for step in reversed(execution_results):
            if step.get("status") == "success":
                response_text = step.get("output") or response_text
                break

    return ChatResponse(
        response=response_text,
        status="success",
        session_id=results.get("session_id"),
    )


def _store_upload(file: UploadFile, content: bytes) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = file.filename or "upload"
    safe_name = safe_name.replace("/", "_").replace("\\", "_")
    target_path = UPLOADS_DIR / f"{timestamp}_{safe_name}"
    with open(target_path, "wb") as f:
        f.write(content)
    return target_path


@app.post("/api/upload")
async def upload_endpoint(
    file: UploadFile = File(...),
    message: Optional[str] = Form(None),
):
    """Handle secure upload of images and PDF files."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a name.")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES and content_type not in ALLOWED_PDF_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only JPG, PNG, and PDF are allowed.")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 10MB size limit.")

    saved_path = _store_upload(file, data)
    logger.info("Stored file at %s", saved_path)

    file_context = None
    file_info = {
        "filename": file.filename,
        "content_type": content_type,
        "size": len(data),
        "saved_path": str(saved_path),
    }

    if content_type in ALLOWED_PDF_TYPES:
        try:
            parsed = pdf_parser.parse_pdf(str(saved_path))
            if parsed.get("success"):
                file_context = parsed.get("text", "")[:5000]
                file_info["word_count"] = parsed.get("metadata", {}).get("word_count")
            else:
                file_info["parse_error"] = parsed.get("error")
        except Exception as exc:
            logger.warning("PDF parsing failed: %s", exc)
            file_info["parse_error"] = "Unable to extract text from PDF."

    response_text = None
    session_id = None
    if message:
        chat_payload = ChatRequest(message=_sanitize_text(message), file_context=file_context)
        chat_response = await chat_endpoint(chat_payload)
        response_text = chat_response.response
        session_id = chat_response.session_id

    preview = None
    if file_context:
        preview = file_context[:500]
        if len(file_context) > 500:
            preview += "..."

    return JSONResponse(
        {
            "status": "success",
            "file": file_info,
            "file_context_preview": preview,
            "response": response_text,
            "session_id": session_id,
        }
    )


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    logger.info("Starting API server on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port)
