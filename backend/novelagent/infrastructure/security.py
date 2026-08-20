from __future__ import annotations

import hashlib
from pathlib import Path


def hash_text(content: str) -> str:
    """Calculate SHA-256 hash of a text string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def is_path_allowed(path: Path, allowed: set[Path]) -> bool:
    """Check if a path is located within authorized directories."""
    resolved = path.resolve()
    return any(resolved == root or root in resolved.parents for root in allowed)
