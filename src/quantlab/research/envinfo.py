"""Research environment metadata. Dirty git worktrees are marked, not hidden."""

from __future__ import annotations

import subprocess
import sys
from typing import Any

from quantlab import __version__


def git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def git_dirty() -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except OSError:
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def environment() -> dict[str, str]:
    payload: dict[str, str] = {
        "python": sys.version.split()[0],
        "quantlab": __version__,
        "platform": sys.platform,
    }
    try:
        import numpy

        payload["numpy"] = numpy.__version__
    except Exception:
        payload["numpy"] = ""
    return payload


def as_lineage_fields() -> dict[str, str]:
    env = environment()
    extra: dict[str, Any] = dict(env)
    extra["git_dirty"] = "true" if git_dirty() else "false"
    return {k: str(v) for k, v in extra.items()}
