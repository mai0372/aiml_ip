"""
backend/app/agents/segmenter.py
Splits legal agreements into numbered or paragraph-based clauses
while maintaining exact character offsets into the source text.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Optional

from backend.app.models.clause_ir import ClauseSpan


class ClauseSegment:
    def __init__(self, clause_id: str, raw_number: Optional[str], text: str, span: ClauseSpan):
        self.clause_id = clause_id
        self.raw_number = raw_number
        self.text = text
        self.span = span

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "raw_number": self.raw_number,
            "text": self.text,
            "span": {"start": self.span.start, "end": self.span.end}
        }


class ContractSegmenter:
    """Segments agreements using hierarchical regex patterns with paragraph fallback."""

    # Matches numbered clause headers:
    # "1.", "1.1", "Clause 4", "Clause IV.", "(a)", "(1)", "First:", "Fourth:"
    HEADER_REGEX = re.compile(
        r"(?:^|\n\n|\n)"
        r"(?P<prefix>"
        r"(?:Clause\s+[0-9IVXLCDMivxlcdm]+[\.\:\s]*[A-Za-z0-9\s]*[\:\.\-]?)"
        r"|(?:\([0-9a-zA-Z]+\)[\.\:\s]*)"
        r"|(?:[0-9]{1,2}(?:\.[0-9]{1,2})*[\.\:\)]\s*)"
        r"|(?:(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth)[\.\:\s]*)"
        r")",
        re.IGNORECASE | re.MULTILINE
    )

    @classmethod
    def segment(cls, text: str) -> List[ClauseSegment]:
        if not text.strip():
            return []

        # Find all clause header match positions
        matches = list(cls.HEADER_REGEX.finditer(text))

        # If too few regex headers found (e.g. unnumbered contract), fallback to double newline paragraphs
        if len(matches) < 2:
            return cls._segment_by_paragraphs(text)

        segments: List[ClauseSegment] = []
        clause_idx = 1

        for i in range(len(matches)):
            curr_match = matches[i]
            prefix_str = curr_match.group("prefix").strip()
            start_pos = curr_match.start()

            # End position is start of next match, or end of text
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            clause_raw_text = text[start_pos:end_pos].strip()
            # Skip boilerplate preamble or witness sections if too short
            if len(clause_raw_text) < 15 and ("witness" in clause_raw_text.lower() or "whereas" in clause_raw_text.lower()):
                continue

            # Strip header prefix from body text
            body_text = clause_raw_text
            clean_prefix = prefix_str.strip()
            if body_text.startswith(clean_prefix):
                body_text = body_text[len(clean_prefix):].strip().lstrip(":-. \t")

            # Extract numeric label if available
            num_match = re.search(r"[0-9]+", clean_prefix)
            clause_num = num_match.group(0) if num_match else str(clause_idx)
            clause_id = f"Clause_{clause_num}"

            # Ensure unique IDs
            if any(s.clause_id == clause_id for s in segments):
                clause_id = f"Clause_{clause_num}_{clause_idx}"

            segments.append(ClauseSegment(
                clause_id=clause_id,
                raw_number=clean_prefix,
                text=body_text if len(body_text) > 10 else clause_raw_text,
                span=ClauseSpan(start=start_pos, end=end_pos)
            ))
            clause_idx += 1

        return segments

    @classmethod
    def _segment_by_paragraphs(cls, text: str) -> List[ClauseSegment]:
        """Paragraph fallback segmenter."""
        paragraphs = re.split(r"\n\s*\n", text)
        segments: List[ClauseSegment] = []
        current_offset = 0

        clause_idx = 1
        for para in paragraphs:
            stripped = para.strip()
            if not stripped:
                current_offset += len(para) + 2
                continue

            start_idx = text.find(stripped, current_offset)
            if start_idx == -1:
                start_idx = current_offset
            end_idx = start_idx + len(stripped)
            current_offset = end_idx

            # Filter out short metadata headers
            if len(stripped) > 25 and not stripped.isupper():
                segments.append(ClauseSegment(
                    clause_id=f"Clause_{clause_idx}",
                    raw_number=f"Para {clause_idx}",
                    text=stripped,
                    span=ClauseSpan(start=start_idx, end=end_idx)
                ))
                clause_idx += 1

        return segments
