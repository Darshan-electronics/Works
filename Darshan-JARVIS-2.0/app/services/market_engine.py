"""Market research and backtesting engine.

Offline-first: accepts OHLCV CSV data and runs deterministic strategies.
Live market APIs are intentionally optional and are not used for execution.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


def load_csv(path: str) -> list[Candle]:
    rows: list[Candle] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(Candle(
                timestamp=r.get("timestamp") or r.get("date") or r.get("datetime") or "",
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=float(r.get("volume") or 0),
            ))
    if len(rows) < 30:
        raise ValueError("At least 30 OHLCV candles are required.")
    return rows


def sma(values: list[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if period <= 0:
        raise ValueError("period must be positive")
    for i in range(period - 1, len(values)):
        out[i] = sum(values[i-period+1:i+1]) / period
    return out


def backtest_sma_cross(candles: list[Candle], fast: int = 10, slow: int = 30,
                       starting_cash: float = 20.0, fee_pct: float = 0.1) -> dict[str, Any]:
    if fast >= slow:
        raise ValueError("fast period must be smaller than slow period")
    closes = [c.close for c in candles]
    f = sma(closes, fast)
    s = sma(closes, slow)

    cash = float(starting_cash)
    qty = 0.0
    entry = 0.0
    trades: list[dict[str, Any]] = []
    equity_curve: list[float] = []

    for i, c in enumerate(candles):
        if f[i] is not None and s[i] is not None and qty == 0 and f[i] > s[i]:
            spend = cash
            qty = spend / c.close
            fee = spend * fee_pct / 100
            cash -= spend + fee
            entry = c.close
            trades.append({"timestamp": c.timestamp, "side": "BUY", "price": c.close, "fee": fee})
        elif f[i] is not None and s[i] is not None and qty > 0 and f[i] < s[i]:
            proceeds = qty * c.close
            fee = proceeds * fee_pct / 100
            pnl = proceeds - fee - (qty * entry)
            cash += proceeds - fee
            trades.append({"timestamp": c.timestamp, "side": "SELL", "price": c.close, "fee": fee, "pnl": pnl})
            qty = 0.0
            entry = 0.0
        equity_curve.append(cash + qty * c.close)

    if qty:
        final_price = candles[-1].close
        proceeds = qty * final_price
        fee = proceeds * fee_pct / 100
        cash += proceeds - fee
        pnl = proceeds - fee - (qty * entry)
        trades.append({"timestamp": candles[-1].timestamp, "side": "SELL_EOD", "price": final_price, "fee": fee, "pnl": pnl})

    final_equity = cash
    total_return_pct = ((final_equity / starting_cash) - 1) * 100
    peak = starting_cash
    max_drawdown_pct = 0.0
    for e in equity_curve:
        peak = max(peak, e)
        if peak:
            max_drawdown_pct = max(max_drawdown_pct, (peak - e) / peak * 100)

    closed = [t["pnl"] for t in trades if "pnl" in t]
    wins = [x for x in closed if x > 0]
    losses = [x for x in closed if x <= 0]
    profit_factor = (sum(wins) / abs(sum(losses))) if losses and sum(losses) else (math.inf if wins else 0.0)

    return {
        "strategy": f"SMA crossover {fast}/{slow}",
        "starting_cash": starting_cash,
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "closed_trades": len(closed),
        "win_rate_pct": (len(wins) / len(closed) * 100) if closed else 0.0,
        "profit_factor": profit_factor,
        "trades": trades,
    }


def compare_strategies(candles: list[Candle], starting_cash: float = 20.0) -> list[dict[str, Any]]:
    configs = [(5, 20), (10, 30), (20, 50)]
    results = [
        backtest_sma_cross(candles, fast=a, slow=b, starting_cash=starting_cash)
        for a, b in configs
    ]
    return sorted(results, key=lambda x: (x["total_return_pct"], -x["max_drawdown_pct"]), reverse=True)
