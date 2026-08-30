"""Disk and process resource checks. Unknown is not healthy."""

from __future__ import annotations

import shutil
from pathlib import Path

from quantlab.ops.errors import OpsError

_INJECTED_FREE: int | None = None


def reset_for_tests() -> None:
    global _INJECTED_FREE
    _INJECTED_FREE = None


def inject_free_bytes(value: int | None) -> None:
    global _INJECTED_FREE
    _INJECTED_FREE = value


def free_bytes(path: Path | None = None) -> int:
    if _INJECTED_FREE is not None:
        return _INJECTED_FREE
    usage = shutil.disk_usage(path or Path.cwd())
    return int(usage.free)


def assert_disk(*, min_free: int, path: Path | None = None) -> int:
    available = free_bytes(path)
    if available < min_free:
        raise OpsError("disk-critical state")
    return available
