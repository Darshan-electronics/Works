import json
import os
import asyncio
import httpx
from .config import AI_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL, OPENAI_API_KEY, OPENAI_MODEL

# Protect the desktop from multiple simultaneous local-model generations.
# One Ollama generation at a time is deliberate: concurrent generations can
# exhaust RAM/VRAM and make Linux appear frozen.
_ollama_lock = asyncio.Semaphore(1)

_HEAVY_MARKERS = ("9b", "14b", "27b", "32b", "34b", "70b", "72b")

def _available_memory_mb():
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except Exception:
        return 0
    return 0

def _ollama_model():
    configured = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL).strip()
    safe = os.getenv("OLLAMA_SAFE_MODEL", "llama3.2:1b").strip()
    allow_heavy = os.getenv("JARVIS_ALLOW_HEAVY_MODEL", "false").strip().lower() in {"1", "true", "yes", "on"}
    if not allow_heavy and any(marker in configured.lower() for marker in _HEAVY_MARKERS):
        return safe
    return configured

def _resource_guard():
    available = _available_memory_mb()
    minimum = int(os.getenv("JARVIS_MIN_FREE_RAM_MB", "2500"))
    if available and available < minimum:
        raise RuntimeError(
            f"JARVIS refused local AI generation because only {available} MB RAM is available "
            f"(minimum {minimum} MB). This prevents Ubuntu from freezing. Close other applications "
            "or use a smaller AI model."
        )

async def _ollama_chat(messages, temperature=0.2):
    model = _ollama_model()
    _resource_guard()
    timeout = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=10.0)

    async with _ollama_lock:
        _resource_guard()
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                r = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "keep_alive": "0",
                        "options": {
                            "temperature": temperature,
                            # Keep context/generation bounded so a local model
                            # cannot consume the machine's memory indefinitely.
                            "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "1024")),
                            "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "256")),
                        },
                    },
                )
                r.raise_for_status()
                data = r.json()
                return data["message"]["content"]
            except httpx.TimeoutException as exc:
                raise RuntimeError(
                    "Local AI timed out. JARVIS stopped the request to protect system resources. "
                    f"Model: {model}. Try a smaller Ollama model."
                ) from exc
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text[:500]
                raise RuntimeError(f"Ollama request failed ({exc.response.status_code}): {detail}") from exc

async def chat(messages, temperature=0.2):
    if AI_PROVIDER == "ollama":
        return await _ollama_chat(messages, temperature)

    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        timeout = httpx.Timeout(connect=10.0, read=75.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={"model": OPENAI_MODEL, "messages": messages,
                      "temperature": temperature},
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    raise RuntimeError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}")

async def answer(question, context):
    system = """You are DARSHAN JARVIS 2.0, a personal engineering assistant.
Use the supplied memory/research context when relevant. Do not invent facts.
If context conflicts with your own knowledge, explain the uncertainty.
Never claim that model weights were retrained. Knowledge is learned by retrieval
and verified notes. For consequential actions, ask for confirmation rather than
performing them."""
    # Do not send an unnecessarily huge prompt to a local model.
    context_text = json.dumps(context, ensure_ascii=False)[:12000]
    return await chat([
        {"role": "system", "content": system},
        {"role": "user", "content": f"Relevant stored knowledge and research:\n{context_text}\n\nQuestion:\n{question}"},
    ])

async def learn_from_research(topic, results):
    evidence = []
    for item in results[:8]:
        evidence.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        })
    prompt = """You are JARVIS's knowledge curator. Turn the supplied web-search
evidence into a compact, technically useful knowledge note. Do not add claims
that are not supported by the evidence. Preserve source URLs. Flag uncertainty.
Return JSON with keys: title, summary, facts, caveats. facts must be a list of
short factual statements."""
    raw = await chat([
        {"role": "system", "content": prompt},
        {"role": "user", "content": json.dumps({"topic": topic, "evidence": evidence}, ensure_ascii=False)},
    ], temperature=0.1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"title": topic, "summary": raw, "facts": [], "caveats": ["Curator output was not valid JSON."]}

async def embed(text):
    if AI_PROVIDER != "ollama":
        return None
    timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={
                "model": os.getenv("OLLAMA_EMBED_MODEL", "embeddinggemma"),
                "input": text,
            },
        )
        if r.is_error:
            return None
        data = r.json()
        return data.get("embeddings", [None])[0]
