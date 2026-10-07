"""JARVIS urgency and escalation policy.

This module decides how an event should reach the user. It deliberately does
not place a call itself; the phone gateway is invoked only after the policy
allows escalation.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from ..config import DB_PATH


LEVELS = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3, "EMERGENCY": 4}


@dataclass
class AlertDecision:
    level: str
    notify: bool
    call: bool
    reason: str
    cooldown_seconds: int


def _init() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS alert_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT NOT NULL,
                level TEXT NOT NULL,
                created_at REAL NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0,
                call_attempted INTEGER NOT NULL DEFAULT 0
            )"""
        )
        db.commit()


def decide(level: str, event_key: str, acknowledged: bool = False) -> AlertDecision:
    _init()
    normalized = level.upper()
    if normalized not in LEVELS:
        normalized = "MEDIUM"

    # Emergency events may call immediately. Critical events call only once
    # and then respect the cooldown. High events never call automatically.
    cooldown = 30 * 60 if normalized == "CRITICAL" else 5 * 60
    now = time.time()

    with sqlite3.connect(DB_PATH) as db:
        recent = db.execute(
            """SELECT id, call_attempted FROM alert_events
               WHERE event_key=? AND created_at>? ORDER BY created_at DESC LIMIT 1""",
            (event_key, now - cooldown),
        ).fetchone()

        if acknowledged:
            return AlertDecision(normalized, True, False, "already acknowledged", cooldown)

        if normalized == "EMERGENCY":
            call = True
            reason = "emergency policy"
        elif normalized == "CRITICAL":
            call = not (recent and recent[1])
            reason = "critical policy"
        else:
            call = False
            reason = "notification-only policy"

        db.execute(
            """INSERT INTO alert_events(event_key, level, created_at, call_attempted)
               VALUES (?, ?, ?, ?)""",
            (event_key, normalized, now, int(call)),
        )
        db.commit()

    return AlertDecision(normalized, True, call, reason, cooldown)
