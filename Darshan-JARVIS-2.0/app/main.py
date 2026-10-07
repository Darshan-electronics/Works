from pathlib import Path
from fastapi import FastAPI, Header, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .config import ACCESS_TOKEN, WEB_RESEARCH_ENABLED, SEARXNG_URL
from .ai import answer, learn_from_research
from .knowledge import init_knowledge, remember, search_knowledge
from .memory import add_memory, search_memories, audit
from .services.web_research import search_web
from .services.work_engine import create_project

app = FastAPI(title="Darshan JARVIS 2.0")
mobile_clients: set[WebSocket] = set()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)

class LearnRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=500)
    save: bool = True

def auth(authorization: str | None):
    if not ACCESS_TOKEN:
        raise HTTPException(503, "JARVIS_ACCESS_TOKEN is not configured")
    if authorization != f"Bearer {ACCESS_TOKEN}":
        raise HTTPException(401, "Invalid JARVIS token")

@app.on_event("startup")
def startup():
    init_knowledge()
    audit("server_start", "LOW", "ok", "JARVIS started")

@app.get("/health")
def health():
    return {"ok": True, "ai": __import__("os").getenv("AI_PROVIDER", "openai"),
            "web_research": WEB_RESEARCH_ENABLED}

@app.get("/")
def index():
    return FileResponse(Path(__file__).resolve().parent.parent / "frontend" / "index.html")

@app.post("/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    auth(authorization)
    memories = search_memories(req.message)
    knowledge = search_knowledge(req.message)
    context = {"memories": memories, "knowledge": knowledge}
    result = await answer(req.message, context)
    audit("chat", "LOW", "ok", req.message[:300])
    return {"answer": result, "memory_hits": len(memories), "knowledge_hits": len(knowledge)}

@app.post("/learn")
async def learn(req: LearnRequest, authorization: str | None = Header(default=None)):
    auth(authorization)
    if not WEB_RESEARCH_ENABLED:
        raise HTTPException(503, "Web research is disabled")
    results = await search_web(req.topic, SEARXNG_URL)
    if not results:
        raise HTTPException(502, "No research results. Check SearXNG.")
    note = await learn_from_research(req.topic, results)
    if req.save:
        source_urls = "\n".join(x.get("url", "") for x in results[:8] if x.get("url"))
        facts = "\n".join(f"- {x}" for x in note.get("facts", []))
        content = f"{note.get('summary','')}\n\nFacts:\n{facts}\n\nCaveats:\n" + "\n".join(f"- {x}" for x in note.get("caveats", []))
        remember(note.get("title", req.topic), content, source="web_research", url=source_urls)
        add_memory("learned_topic", f"Learned about {req.topic}", source="web_research", confidence=0.7, approved=True)
        audit("learn", "MEDIUM", "saved", req.topic)
    return {"topic": req.topic, "note": note, "sources": results[:8], "saved": req.save}



class PhoneCallRequest(BaseModel):
    to_number: str = Field(min_length=8, max_length=32)
    confirmed: bool = False


@app.websocket("/mobile/events")
async def mobile_events(websocket: WebSocket):
    auth_header = websocket.headers.get("authorization")
    if not ACCESS_TOKEN or auth_header != "Bearer " + ACCESS_TOKEN:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    await websocket.accept()
    mobile_clients.add(websocket)
    try:
        await websocket.send_json({"type": "connected", "service": "jarvis", "message": "JARVIS mobile event channel connected"})
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        mobile_clients.discard(websocket)

@app.post("/phone/call")
async def phone_call(req: PhoneCallRequest, authorization: str | None = Header(default=None)):
    auth(authorization)
    if not req.confirmed:
        raise HTTPException(409, "Phone call requires explicit confirmation.")
    from .services.phone_gateway import create_call
    result = await create_call(req.to_number)
    audit("phone_call", "HIGH", "started", req.to_number[-4:])
    return {"ok": True, "call": result}


@app.websocket("/phone/media")
async def phone_media(websocket: WebSocket):
    await websocket.accept()
    from .services.realtime_phone import run_call_bridge
    try:
        opening = websocket.query_params.get("opening", "")
        await run_call_bridge(websocket, answer, opening_message=opening)
    except Exception as exc:
        audit("phone_media", "HIGH", "error", str(exc)[:300])
        try:
            await websocket.close(code=1011)
        except Exception:
            pass

@app.post("/phone/twiml/start")
async def phone_twiml_start(opening: str = ""):
    from .services.phone_gateway import start_twiml
    return start_twiml(opening)

@app.post("/phone/twiml/turn")
async def phone_twiml_turn(
    SpeechResult: str = "",
    CallSid: str = "",
):
    from .services.phone_gateway import turn_twiml
    return await turn_twiml(SpeechResult, CallSid, answer)

@app.post("/phone/status")
async def phone_status(
    CallSid: str = "",
    CallStatus: str = "",
    CallDuration: str = "",
    From: str = "",
    To: str = "",
):
    from .services.phone_gateway import status
    payload = status({
        "CallSid": CallSid,
        "CallStatus": CallStatus,
        "CallDuration": CallDuration,
        "From": From,
        "To": To,
    })
    audit("phone_status", "LOW", CallStatus or "unknown", CallSid)
    return {"ok": True, "status": payload}



class AlertRequest(BaseModel):
    event_key: str = Field(min_length=2, max_length=200)
    level: str = Field(default="MEDIUM", max_length=20)
    message: str = Field(min_length=1, max_length=4000)
    confirmed: bool = False

@app.post("/alerts/evaluate")
async def evaluate_alert(req: AlertRequest, authorization: str | None = Header(default=None)):
    auth(authorization)
    from .services.urgency import decide
    decision = decide(req.level, req.event_key)
    call_result = None

    if decision.call:
        from .services.phone_gateway import create_call
        target = __import__("os").getenv("JARVIS_PHONE_NUMBER", "")
        if not target:
            raise HTTPException(503, "JARVIS_PHONE_NUMBER is not configured")
        call_result = await create_call(target, f"Important JARVIS alert: {req.message}")

    event = {"type": "alert", "event_key": req.event_key, "level": decision.level, "message": req.message, "call": decision.call}
    stale = []
    for client in mobile_clients:
        try:
            await client.send_json(event)
        except Exception:
            stale.append(client)
    for client in stale:
        mobile_clients.discard(client)
    audit("alert", decision.level, decision.reason, req.event_key)
    return {
        "level": decision.level,
        "notify": decision.notify,
        "call": decision.call,
        "reason": decision.reason,
        "message": req.message,
        "call_result": call_result,
    }

class WorkRequest(BaseModel):
    request: str = Field(min_length=5, max_length=12000)

@app.post("/trading/market-snapshot")
def trading_market_snapshot(req: dict):
    candles = load_csv(req["csv_path"])
    return technical_snapshot(candles)


@app.post("/trading/walk-forward")
def trading_walk_forward(req: dict):
    candles = load_csv(req["csv_path"])
    return walk_forward_sma(
        candles,
        train_size=int(req.get("train_size", 100)),
        test_size=int(req.get("test_size", 30)),
        starting_cash=float(req.get("starting_cash", 20.0)),
    )


@app.post("/trading/paper-signal")
def trading_paper_signal(req: dict):
    candles = load_csv(req["csv_path"])
    return paper_signal(candles)


@app.post("/trading/fetch-csv")
def trading_fetch_csv(req: dict):
    rows = normalize_ohlcv(fetch_csv_url(req["url"]))
    return {"rows": rows, "count": len(rows), "warning": "Verify provider, symbol, timezone and data quality before use."}


@app.post("/trading/backtest")
def trading_backtest(req: dict):
    candles = load_csv(req["csv_path"])
    return backtest_sma_cross(
        candles,
        fast=int(req.get("fast", 10)),
        slow=int(req.get("slow", 30)),
        starting_cash=float(req.get("starting_cash", 20.0)),
        fee_pct=float(req.get("fee_pct", 0.1)),
    )


@app.post("/trading/compare")
def trading_compare(req: dict):
    candles = load_csv(req["csv_path"])
    return compare_strategies(candles, starting_cash=float(req.get("starting_cash", 20.0)))


@app.get("/trading/status")
def trading_status():
    return TradingEngine().status()


@app.post("/trading/propose")
def trading_propose(req: dict):
    engine = TradingEngine()
    return engine.propose(
        symbol=req["symbol"],
        price=float(req["price"]),
        stop=float(req["stop"]),
        target=float(req["target"]),
        quantity=float(req.get("quantity", 1.0)),
        strategy=req.get("strategy", "manual-research"),
        rationale=req.get("rationale", ""),
    )


@app.post("/trading/paper-buy")
def trading_paper_buy(req: dict):
    engine = TradingEngine()
    return engine.paper_buy(
        symbol=req["symbol"],
        price=float(req["price"]),
        stop=float(req["stop"]),
        target=float(req["target"]),
        quantity=float(req.get("quantity", 1.0)),
        strategy=req.get("strategy", "manual-research"),
        rationale=req.get("rationale", ""),
    )


@app.post("/trading/paper-sell")
def trading_paper_sell(req: dict):
    return TradingEngine().paper_sell(
        symbol=req["symbol"],
        price=float(req["price"]),
        strategy=req.get("strategy", "manual-research"),
    )


@app.get("/trading/history")
def trading_history(limit: int = 50):
    return TradingEngine().history(limit)


@app.get("/quantum/status")
def quantum_backend_status():
    return quantum_status()


@app.post("/quantum/analyze")
def quantum_analyze(req: WorkRequest):
    return analyze_algorithm(req.request)


@app.post("/quantum/vlsi-plan")
def quantum_vlsi(req: WorkRequest):
    return quantum_vlsi_plan(req.request)


@app.post("/quantum/bell")
def quantum_bell():
    return bell_state()


@app.post("/artifacts/project")
async def create_artifacts(req: WorkRequest, authorization: str | None = Header(default=None)):
    auth(authorization)
    result = await create_project(req.request)
    audit("artifact_project", "MEDIUM", "created", result["name"])
    return result

@app.post("/artifacts/validate")
async def validate_artifacts(req: WorkRequest, authorization: str | None = Header(default=None)):
    auth(authorization)
    from .services.validation import validate_project
    result = validate_project(req.request)
    audit("artifact_validation", "LOW", "completed", req.request[:200])
    return result

@app.get("/knowledge")
def knowledge(q: str = "", authorization: str | None = Header(default=None)):
    auth(authorization)
    return {"results": search_knowledge(q, 20) if q.strip() else []}

@app.get("/memory")
def memory(q: str = "", authorization: str | None = Header(default=None)):
    auth(authorization)
    return {"results": search_memories(q, 20) if q.strip() else []}
