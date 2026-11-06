"""
backend/app/agents/ingest.py
Document ingestion, text normalization, and optional Indian PII redaction.
Supports raw text, PDF (pdfplumber), and Word (.docx).
"""

from __future__ import annotations
import re
import io
from typing import Tuple, Optional
import docx
import pdfplumber


class PIIFilter:
    """Detects and redacts Indian Personally Identifiable Information (PII)."""

    # Indian mobile: +91 or standard 10-digit starting with 6, 7, 8, 9
    PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}\b")
    # Email
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    # Aadhaar: 12 digits, often in 4-4-4 format
    AADHAAR_REGEX = re.compile(r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b")
    # PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
    PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")

    @classmethod
    def redact(cls, text: str) -> Tuple[str, int]:
        """Redacts PII patterns and returns the sanitized text and count of redactions."""
        count = 0

        def replace_phone(m):
            nonlocal count
            count += 1
            return "[PHONE_REDACTED]"

        def replace_email(m):
            nonlocal count
            count += 1
            return "[EMAIL_REDACTED]"

        def replace_aadhaar(m):
            nonlocal count
            count += 1
            return "[AADHAAR_REDACTED]"

        def replace_pan(m):
            nonlocal count
            count += 1
            return "[PAN_REDACTED]"

        redacted = cls.PHONE_REGEX.sub(replace_phone, text)
        redacted = cls.EMAIL_REGEX.sub(replace_email, redacted)
        redacted = cls.AADHAAR_REGEX.sub(replace_aadhaar, redacted)
        redacted = cls.PAN_REGEX.sub(replace_pan, redacted)

        return redacted, count


class DocumentIngester:
    """Ingests files or text, normalizes typography, and applies optional privacy filters."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes unicode quotes, hyphens, non-breaking spaces, and whitespace."""
        # Normalize smart quotes
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        # Normalize dashes
        text = text.replace("—", "-").replace("–", "-")
        # Normalize non-breaking spaces and tabs
        text = text.replace("\xa0", " ").replace("\t", " ")
        # Normalize multiple spaces on same line
        lines = [re.sub(r" +", " ", line).strip() for line in text.splitlines()]
        return "\n".join(lines).strip()

    @classmethod
    def extract_from_bytes(cls, file_bytes: bytes, filename: str) -> str:
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return cls.extract_from_pdf(file_bytes)
        elif lower_name.endswith(".docx"):
            return cls.extract_from_docx(file_bytes)
        else:
            # Default to UTF-8 plain text
            return file_bytes.decode("utf-8", errors="replace")

    @classmethod
    def extract_from_docx(cls, file_bytes: bytes) -> str:
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    @classmethod
    def extract_from_pdf(cls, file_bytes: bytes) -> str:
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
        return "\n\n".join(text_parts)

    @classmethod
    def process(cls, raw_text: str, redact_pii: bool = False) -> Tuple[str, dict]:
        clean_text = cls.normalize_text(raw_text)
        metadata = {"original_length": len(raw_text), "clean_length": len(clean_text), "redactions": 0}
        if redact_pii:
            clean_text, count = PIIFilter.redact(clean_text)
            metadata["redactions"] = count
        return clean_text, metadata
