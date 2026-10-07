import os
import httpx

API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

async def synthesize(text: str, voice_id: str | None = None) -> bytes:
    key = os.getenv("ELEVENLABS_API_KEY", "")
    voice = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured")
    if not voice:
        raise RuntimeError("ELEVENLABS_VOICE_ID is not configured")
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            f"{API_URL}/{voice}",
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": os.getenv("ELEVENLABS_MODEL", "eleven_v3"),
                "output_format": "mp3_44100_128",
            },
        )
        r.raise_for_status()
        return r.content
