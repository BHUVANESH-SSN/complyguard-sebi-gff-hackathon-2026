"""Split cleaned circular text into individual numbered-clause chunks."""
import re

CLAUSE_PATTERN = re.compile(r"(?m)^(?=\d+(?:\.\d+)*\.?\s+\S)")


def split_into_clauses(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    pieces = CLAUSE_PATTERN.split(text)
    clauses = [p.strip() for p in pieces if p.strip()]

    if len(clauses) <= 1:
        clauses = [p.strip() for p in text.split("\n\n") if p.strip()]

    return clauses
