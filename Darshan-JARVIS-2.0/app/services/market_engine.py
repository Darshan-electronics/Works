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



def ema(values: list[float], period: int) -> list[float | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    alpha = 2.0 / (period + 1)
    prev = seed
    for i in range(period, len(values)):
        prev = alpha * values[i] + (1 - alpha) * prev
        out[i] = prev
    return out


def rsi(values: list[float], period: int = 14) -> list[float | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return out
    gains = [max(values[i] - values[i-1], 0.0) for i in range(1, len(values))]
    losses = [max(values[i-1] - values[i], 0.0) for i in range(1, len(values))]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    def value(g: float, l: float) -> float:
        if l == 0:
            return 100.0
        rs = g / l
        return 100.0 - (100.0 / (1.0 + rs))
    out[period] = value(avg_gain, avg_loss)
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        out[i + 1] = value(avg_gain, avg_loss)
    return out


def atr(candles: list[Candle], period: int = 14) -> list[float | None]:
    if len(candles) <= period:
        return [None] * len(candles)
    trs = [0.0]
    for i in range(1, len(candles)):
        c, prev = candles[i], candles[i-1]
        trs.append(max(c.high-c.low, abs(c.high-prev.close), abs(c.low-prev.close)))
    out: list[float | None] = [None] * len(candles)
    prev_atr = sum(trs[1:period+1]) / period
    out[period] = prev_atr
    for i in range(period + 1, len(candles)):
        prev_atr = ((prev_atr * (period - 1)) + trs[i]) / period
        out[i] = prev_atr
    return out


def technical_snapshot(candles: list[Candle]) -> dict[str, Any]:
    closes = [c.close for c in candles]
    fast = sma(closes, 10)[-1]
    slow = sma(closes, 30)[-1]
    e20 = ema(closes, 20)[-1]
    r14 = rsi(closes, 14)[-1]
    a14 = atr(candles, 14)[-1]
    return {
        "last_timestamp": candles[-1].timestamp,
        "close": closes[-1],
        "sma10": fast,
        "sma30": slow,
        "ema20": e20,
        "rsi14": r14,
        "atr14": a14,
        "signal": (
            "bullish" if fast is not None and slow is not None and fast > slow and (r14 is None or r14 < 70)
            else "bearish" if fast is not None and slow is not None and fast < slow
            else "neutral"
        ),
    }


def walk_forward_sma(candles: list[Candle], train_size: int = 100, test_size: int = 30,
                     starting_cash: float = 20.0) -> dict[str, Any]:
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    windows = []
    start = 0
    while start + train_size + test_size <= len(candles):
        train = candles[start:start+train_size]
        test = candles[start+train_size:start+train_size+test_size]
        candidates = compare_strategies(train, starting_cash=starting_cash)
        chosen = candidates[0]
        fast, slow = (int(x) for x in chosen["strategy"].split()[-1].split("/"))
        forward = backtest_sma_cross(test, fast=fast, slow=slow, starting_cash=starting_cash)
        windows.append({
            "train_start": train[0].timestamp,
            "train_end": train[-1].timestamp,
            "test_start": test[0].timestamp,
            "test_end": test[-1].timestamp,
            "selected_strategy": chosen["strategy"],
            "forward_result": {
                "return_pct": forward["total_return_pct"],
                "max_drawdown_pct": forward["max_drawdown_pct"],
                "win_rate_pct": forward["win_rate_pct"],
                "profit_factor": forward["profit_factor"],
            },
        })
        start += test_size
    if not windows:
        raise ValueError("Not enough data for walk-forward testing.")
    returns = [w["forward_result"]["return_pct"] for w in windows]
    return {
        "method": "walk_forward",
        "windows": windows,
        "average_forward_return_pct": sum(returns) / len(returns),
        "profitable_windows_pct": sum(r > 0 for r in returns) / len(returns) * 100,
        "warning": "Walk-forward results are historical/forward-simulation evidence, not a guarantee of future returns.",
    }


def paper_signal(candles: list[Candle]) -> dict[str, Any]:
    snap = technical_snapshot(candles)
    price = float(snap["close"])
    a = snap["atr14"] or max(price * 0.005, 0.01)
    if snap["signal"] != "bullish":
        return {"action": "NO_TRADE", "reason": "No bullish confirmation.", "snapshot": snap}
    stop = price - 1.5 * a
    target = price + 3.0 * a
    return {
        "action": "PAPER_BUY_CANDIDATE",
        "price": price,
        "stop": stop,
        "target": target,
        "reward_risk": 2.0,
        "snapshot": snap,
        "warning": "Signal is for paper trading only.",
    }
