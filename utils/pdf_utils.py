"""PDF text extraction and chunking."""
from io import BytesIO

import pdfplumber

from . import config


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF's raw bytes.

    Pages are joined with double newlines. Pages with no extractable text
    (e.g. a scanned image with no OCR layer) simply contribute nothing --
    this app does not perform OCR.
    """
    text_parts = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n\n".join(text_parts).strip()


def chunk_text(text: str, max_chars: int = None) -> list:
    """Split long text into chunks that fit comfortably inside one LLM call.

    Splits on paragraph boundaries (blank lines) where possible so a claim's
    surrounding context usually stays inside a single chunk.
    """
    max_chars = max_chars or config.CHUNK_MAX_CHARS
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks, current = [], ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks
