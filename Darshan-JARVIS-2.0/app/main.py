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

app = FastAPI(title="Darshan JARVIS 2.0")
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

    audit("alert", decision.level, decision.reason, req.event_key)
    return {
        "level": decision.level,
        "notify": decision.notify,
        "call": decision.call,
        "reason": decision.reason,
        "message": req.message,
        "call_result": call_result,
    }

@app.get("/knowledge")
def knowledge(q: str = "", authorization: str | None = Header(default=None)):
    auth(authorization)
    return {"results": search_knowledge(q, 20) if q.strip() else []}

@app.get("/memory")
def memory(q: str = "", authorization: str | None = Header(default=None)):
    auth(authorization)
    return {"results": search_memories(q, 20) if q.strip() else []}
