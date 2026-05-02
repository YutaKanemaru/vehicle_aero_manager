"""Shared filename utilities."""
from __future__ import annotations
import re


def safe_filename(name: str) -> str:
    """Convert an arbitrary string into a safe filesystem filename (no extension).

    Rules:
    - Spaces → underscore
    - Characters illegal on Windows/Linux/macOS (/ \\ : * ? " < > |) → removed
    - Leading/trailing whitespace and dots stripped
    - Truncated to 200 characters
    - Falls back to "file" if result is empty
    """
    result = name.replace(" ", "_")
    result = re.sub(r'[/\\:*?"<>|]', "", result)
    result = result.strip(". ")
    result = result[:200]
    return result or "file"
