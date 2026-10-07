"""JARVIS trading engine.

Research + paper trading first. Real-money execution is intentionally not
implemented here. Every strategy decision is recorded and hard risk limits
prevent the engine from treating a daily profit target as a reason to trade.
"""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RiskConfig:
    starting_capital: float = 20.0
    max_risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 3.0
    max_open_positions: int = 1
    min_reward_risk: float = 2.0
    profit_target_is_required: bool = False


class TradingEngine:
    def __init__(self, db_path: str = "data/trading.sqlite3", config: RiskConfig | None = None):
        self.config = config or RiskConfig()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS paper_account (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            cash REAL NOT NULL,
            equity REAL NOT NULL,
            starting_capital REAL NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS paper_positions (
            symbol TEXT PRIMARY KEY,
            quantity REAL NOT NULL,
            entry_price REAL NOT NULL,
            stop_price REAL NOT NULL,
            target_price REAL NOT NULL,
            opened_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            pnl REAL NOT NULL DEFAULT 0,
            mode TEXT NOT NULL,
            strategy TEXT NOT NULL,
            rationale TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            score REAL NOT NULL,
            reward_risk REAL NOT NULL,
            rationale TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        """)
        row = self.db.execute("SELECT id FROM paper_account WHERE id=1").fetchone()
        if row is None:
            now = self._now()
            self.db.execute(
                "INSERT INTO paper_account(id,cash,equity,starting_capital,updated_at) VALUES(1,?,?,?,?)",
                (self.config.starting_capital, self.config.starting_capital, self.config.starting_capital, now),
            )
            self.db.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def status(self) -> dict[str, Any]:
        a = self.db.execute("SELECT * FROM paper_account WHERE id=1").fetchone()
        positions = [dict(r) for r in self.db.execute("SELECT * FROM paper_positions").fetchall()]
        return {"mode": "paper", "account": dict(a), "positions": positions, "risk": self.config.__dict__}

    def reset(self, capital: float | None = None) -> dict[str, Any]:
        amount = self.config.starting_capital if capital is None else float(capital)
        if amount <= 0:
            raise ValueError("Capital must be positive.")
        self.db.execute("DELETE FROM paper_positions")
        self.db.execute("UPDATE paper_account SET cash=?, equity=?, starting_capital=?, updated_at=? WHERE id=1",
                        (amount, amount, amount, self._now()))
        self.db.commit()
        return self.status()

    def risk_check(self, entry: float, stop: float, target: float, quantity: float) -> dict[str, Any]:
        if entry <= 0 or stop <= 0 or target <= 0 or quantity <= 0:
            return {"allowed": False, "reason": "Prices and quantity must be positive."}
        risk_per_unit = abs(entry - stop)
        reward_per_unit = abs(target - entry)
        rr = reward_per_unit / risk_per_unit if risk_per_unit else 0.0
        account = self.db.execute("SELECT cash FROM paper_account WHERE id=1").fetchone()
        risk_amount = risk_per_unit * quantity
        max_risk = float(account["cash"]) * self.config.max_risk_per_trade_pct / 100
        if rr < self.config.min_reward_risk:
            return {"allowed": False, "reason": "Reward/risk below configured minimum.", "reward_risk": rr}
        if risk_amount > max_risk:
            return {"allowed": False, "reason": "Trade exceeds per-trade risk limit.", "risk_amount": risk_amount, "max_risk": max_risk}
        open_count = self.db.execute("SELECT COUNT(*) AS n FROM paper_positions").fetchone()["n"]
        if open_count >= self.config.max_open_positions:
            return {"allowed": False, "reason": "Maximum open positions reached."}
        return {"allowed": True, "reward_risk": rr, "risk_amount": risk_amount, "max_risk": max_risk}

    def propose(self, symbol: str, price: float, stop: float, target: float, quantity: float = 1.0,
                strategy: str = "manual-research", rationale: str = "") -> dict[str, Any]:
        check = self.risk_check(price, stop, target, quantity)
        action = "PAPER_BUY" if check["allowed"] else "NO_TRADE"
        score = min(100.0, max(0.0, check.get("reward_risk", 0.0) * 25.0))
        self.db.execute(
            "INSERT INTO decisions(symbol,action,score,reward_risk,rationale,timestamp) VALUES(?,?,?,?,?,?)",
            (symbol.upper(), action, score, float(check.get("reward_risk", 0.0)), rationale or check.get("reason", ""), self._now()),
        )
        self.db.commit()
        return {"action": action, "symbol": symbol.upper(), "score": score, "strategy": strategy, "risk": check,
                "rationale": rationale or check.get("reason", "Risk checks passed.")}

    def paper_buy(self, symbol: str, price: float, stop: float, target: float, quantity: float = 1.0,
                  strategy: str = "manual-research", rationale: str = "") -> dict[str, Any]:
        proposal = self.propose(symbol, price, stop, target, quantity, strategy, rationale)
        if proposal["action"] != "PAPER_BUY":
            return proposal
        account = self.db.execute("SELECT cash FROM paper_account WHERE id=1").fetchone()
        cost = price * quantity
        if cost > float(account["cash"]):
            return {"action": "NO_TRADE", "reason": "Insufficient paper cash.", "cash": float(account["cash"])}
        now = self._now()
        self.db.execute("UPDATE paper_account SET cash=cash-?, updated_at=? WHERE id=1", (cost, now))
        self.db.execute(
            "INSERT OR REPLACE INTO paper_positions(symbol,quantity,entry_price,stop_price,target_price,opened_at) VALUES(?,?,?,?,?,?)",
            (symbol.upper(), quantity, price, stop, target, now),
        )
        self.db.execute(
            "INSERT INTO trades(symbol,side,quantity,price,pnl,mode,strategy,rationale,timestamp) VALUES(?,?,?,?,?,?,?,?,?)",
            (symbol.upper(), "BUY", quantity, price, 0.0, "paper", strategy, rationale, now),
        )
        self.db.commit()
        return {"action": "PAPER_BUY_EXECUTED", "symbol": symbol.upper(), "quantity": quantity, "price": price, "cash_remaining": float(account["cash"]) - cost}

    def paper_sell(self, symbol: str, price: float, strategy: str = "manual-research") -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM paper_positions WHERE symbol=?", (symbol.upper(),)).fetchone()
        if row is None:
            return {"action": "NO_TRADE", "reason": "No open paper position."}
        pnl = (price - float(row["entry_price"])) * float(row["quantity"])
        now = self._now()
        self.db.execute("UPDATE paper_account SET cash=cash+?, equity=cash+?, updated_at=? WHERE id=1",
                        (price * float(row["quantity"]), price * float(row["quantity"]), now))
        self.db.execute("DELETE FROM paper_positions WHERE symbol=?", (symbol.upper(),))
        self.db.execute(
            "INSERT INTO trades(symbol,side,quantity,price,pnl,mode,strategy,rationale,timestamp) VALUES(?,?,?,?,?,?,?,?,?)",
            (symbol.upper(), "SELL", row["quantity"], price, pnl, "paper", strategy, "Paper position closed.", now),
        )
        self.db.commit()
        return {"action": "PAPER_SELL_EXECUTED", "symbol": symbol.upper(), "price": price, "pnl": pnl}

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)).fetchall()
        return [dict(r) for r in rows]


def trading_status() -> dict[str, Any]:
    return TradingEngine().status()
