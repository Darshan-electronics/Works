"""Automated paper-trading runner.

This runner only creates paper trades. It never submits orders to a broker.
It is designed to be called periodically by JARVIS/cron/systemd.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.market_engine import Candle, paper_signal
from app.services.trading_engine import TradingEngine


def run_paper_cycle(candles: list[Candle], symbol: str, quantity: float = 1.0) -> dict[str, Any]:
    if not candles:
        return {"action": "NO_TRADE", "reason": "No market data."}

    signal = paper_signal(candles)
    engine = TradingEngine()

    if signal["action"] != "PAPER_BUY_CANDIDATE":
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol.upper(),
            "action": "NO_TRADE",
            "signal": signal,
        }

    result = engine.paper_buy(
        symbol=symbol,
        price=float(signal["price"]),
        stop=float(signal["stop"]),
        target=float(signal["target"]),
        quantity=quantity,
        strategy="SMA10-SMA30+RSI+ATR",
        rationale="Automated paper signal passed technical and risk checks.",
    )
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol.upper(),
        "signal": signal,
        "execution": result,
    }


def daily_report() -> dict[str, Any]:
    engine = TradingEngine()
    status = engine.status()
    history = engine.history(500)
    closed = [t for t in history if t.get("side") in ("SELL", "SELL_EOD")]
    pnl = sum(float(t.get("pnl", 0.0)) for t in closed)
    wins = sum(1 for t in closed if float(t.get("pnl", 0.0)) > 0)
    return {
        "mode": "paper",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "account": status["account"],
        "open_positions": status["positions"],
        "closed_trade_count": len(closed),
        "realized_pnl": pnl,
        "win_rate_pct": (wins / len(closed) * 100) if closed else 0.0,
        "note": "Performance report only; not a forecast or guarantee.",
    }
