"""Small utilities shared by the SafeCart API and agents."""

import math
from collections.abc import Mapping
from datetime import date, datetime
from numbers import Integral, Real
from typing import Any


def normalize_identifier(value: Any) -> str:
    """Normalize an order or product ID for case-insensitive comparisons."""
    if value is None:
        return ""
    return str(value).strip().upper()


def clean_text(value: Any) -> str:
    """Convert optional input to trimmed text, treating null values as empty."""
    return "" if value is None else str(value).strip()


def to_json_safe(value: Any) -> Any:
    """Recursively convert common pandas/NumPy values to JSON-safe values.

    CSV data can contain NaN, NumPy scalar types, timestamps, and nested
    containers. Non-finite numbers become ``None`` so JSON serialization
    produces ``null`` instead of failing.
    """
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        number = float(value)
        return number if math.isfinite(number) else None
    # Handle pandas.NA / NaT without requiring pandas as a utility dependency.
    if type(value).__name__ in {"NAType", "NaTType"}:
        return None
    if isinstance(value, Mapping):
        return {str(key): to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_safe(item) for item in value]
    # NumPy scalar types expose item(); ordinary project objects do not.
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return to_json_safe(item())
        except (ValueError, TypeError):
            pass
    return value
