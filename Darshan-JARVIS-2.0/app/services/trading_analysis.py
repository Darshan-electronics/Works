from __future__ import annotations
import csv, io, math
from pathlib import Path
from urllib.request import Request, urlopen

def load_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    out=[]
    for r in rows:
        try:
            out.append({k.lower(): float(v) if k.lower() not in ("timestamp","date","datetime") else v for k,v in r.items()})
        except (TypeError,ValueError):
            continue
    return out

def _close(row):
    for k in ("close","adj close","adj_close"):
        if k in row: return float(row[k])
    raise ValueError("CSV needs a close column")

def technical_snapshot(candles):
    closes=[_close(r) for r in candles]
    if not closes: return {"ok":False,"error":"No candles"}
    def sma(n): return sum(closes[-n:])/min(n,len(closes))
    return {"ok":True,"count":len(closes),"last":closes[-1],"sma20":sma(20),"sma50":sma(50),
            "change_pct":((closes[-1]/closes[0])-1)*100 if closes[0] else 0}

def paper_signal(candles):
    s=technical_snapshot(candles)
    if not s.get("ok"): return s
    action="BUY" if s["last"]>s["sma20"]>s["sma50"] else "WAIT"
    return {"ok":True,"action":action,"snapshot":s,"mode":"paper"}

def backtest_sma_cross(candles, fast=10, slow=30, starting_cash=20.0, fee_pct=0.1):
    closes=[_close(r) for r in candles]
    cash=float(starting_cash); qty=0.0; entry=0.0; trades=[]
    for i,p in enumerate(closes):
        if i<slow: continue
        f=sum(closes[i-fast+1:i+1])/fast; s=sum(closes[i-slow+1:i+1])/slow
        if qty==0 and f>s and cash>0:
            qty=(cash*(1-fee_pct/100))/p; entry=p; cash=0
            trades.append({"side":"BUY","price":p,"index":i})
        elif qty>0 and f<s:
            cash=qty*p*(1-fee_pct/100); trades.append({"side":"SELL","price":p,"index":i,"pnl":qty*(p-entry)}); qty=0
    equity=cash+qty*(closes[-1] if closes else 0)
    return {"mode":"backtest","starting_cash":starting_cash,"ending_equity":equity,
            "return_pct":((equity/starting_cash)-1)*100 if starting_cash else 0,"trades":trades}

def walk_forward_sma(candles, train_size=100, test_size=30, starting_cash=20.0):
    if len(candles)<train_size+test_size: return {"ok":False,"error":"Not enough candles"}
    return {"ok":True,"note":"Baseline walk-forward scaffold; validate strategy and data before use.",
            "train_size":train_size,"test_size":test_size,
            "result":backtest_sma_cross(candles[train_size:],starting_cash=starting_cash)}

def compare_strategies(candles, starting_cash=20.0):
    return {"sma_10_30":backtest_sma_cross(candles,10,30,starting_cash),
            "sma_5_20":backtest_sma_cross(candles,5,20,starting_cash)}

def run_paper_cycle(candles, symbol, quantity=1.0):
    return {"symbol":symbol.upper(),"signal":paper_signal(candles),"quantity":quantity,"mode":"paper"}

def daily_report():
    return {"mode":"paper","status":"research_only","message":"Use TradingEngine status/history for the local paper account."}

def fetch_csv_url(url):
    req=Request(url,headers={"User-Agent":"Darshan-JARVIS/2.0"})
    with urlopen(req,timeout=20) as r:
        return r.read().decode("utf-8")

def normalize_ohlcv(text):
    return list(csv.DictReader(io.StringIO(text)))
