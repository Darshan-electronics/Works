"""Optional public market-data adapters.

No credentials are required for the CSV adapter. HTTP adapters are deliberately
small and should be configured with a trusted provider before production use.
"""
from __future__ import annotations

import csv
import io
from typing import Any
import httpx


def csv_text_to_rows(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    return [dict(r) for r in reader]


def fetch_csv_url(url: str, timeout: float = 15.0) -> list[dict[str, Any]]:
    r = httpx.get(url, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    return csv_text_to_rows(r.text)


def normalize_ohlcv(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        out.append({
            "timestamp": r.get("timestamp") or r.get("date") or r.get("datetime") or "",
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r.get("volume") or 0),
        })
    return out
