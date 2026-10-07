import json
import httpx
from .config import AI_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL, OPENAI_API_KEY, OPENAI_MODEL

async def chat(messages, temperature=0.2):
    if AI_PROVIDER == "ollama":
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": OLLAMA_MODEL, "messages": messages, "stream": False,
                      "options": {"temperature": temperature}},
            )
            r.raise_for_status()
            data = r.json()
            return data["message"]["content"]
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=180) as client:
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
    context_text = json.dumps(context, ensure_ascii=False)[:50000]
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
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/embed",
                              json={"model": __import__("os").getenv("OLLAMA_EMBED_MODEL", "embeddinggemma"),
                                    "input": text})
        if r.is_error:
            return None
        data = r.json()
        return data.get("embeddings", [None])[0]
