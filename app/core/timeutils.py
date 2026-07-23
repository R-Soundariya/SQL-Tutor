"""Shared time helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Current UTC time as a naive datetime (matches the naive DateTime
    columns used throughout the app) - avoids the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
