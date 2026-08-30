"""IST-relative timestamps for journal and logs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def parse_iso(ts: str) -> datetime | None:
    cleaned = ts.strip()
    if not cleaned:
        return None
    try:
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def format_ist(ts: datetime) -> str:
    local = ts.astimezone(IST)
    return local.strftime("%d %b %Y, %I:%M %p IST")


def format_ist_relative(ts: datetime, *, now: datetime | None = None) -> str:
    reference = now or datetime.now(tz=UTC)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    delta = reference - ts.astimezone(UTC)
    if delta < timedelta(minutes=1):
        return "just now"
    if delta < timedelta(hours=1):
        mins = int(delta.total_seconds() // 60)
        return f"{mins} min ago"
    if delta < timedelta(hours=24):
        hours = int(delta.total_seconds() // 3600)
        return f"{hours} hr ago" if hours == 1 else f"{hours} hrs ago"
    if delta < timedelta(days=7):
        days = delta.days
        return f"{days} day ago" if days == 1 else f"{days} days ago"
    return format_ist(ts)


def format_ist_from_iso(ts: str, *, relative: bool = True) -> str:
    parsed = parse_iso(ts)
    if parsed is None:
        return ts
    if relative:
        return format_ist_relative(parsed)
    return format_ist(parsed)
