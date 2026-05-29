"""Tiny helper for writing values to GITHUB_OUTPUT inside CI.

Used by the starter scripts and fetch_artifacts so the workflow can pipe
conversation IDs and artifact paths between steps without grepping stdout.
"""

from __future__ import annotations

import os
from pathlib import Path


def emit(key: str, value: str) -> None:
    """Write `key=value` to $GITHUB_OUTPUT if set; otherwise no-op."""
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    # Multi-line values would need the heredoc syntax; we only write
    # short scalars (conversation IDs, paths), so a plain key=value is fine.
    with Path(out_path).open("a", encoding="utf-8") as fh:
        fh.write(f"{key}={value}\n")
