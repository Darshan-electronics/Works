"""Twilio phone gateway for JARVIS.

Secrets stay server-side. The public Twilio webhooks should be exposed only
through authenticated HTTPS/reverse-proxy controls in production.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import os
from pathlib import Path

import httpx
from fastapi import HTTPException
from fastapi.responses import Response

AUDIO_DIR = Path(os.getenv("JARVIS_AUDIO_DIR", "data/phone_audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
JARVIS_PUBLIC_BASE_URL = os.getenv("JARVIS_PUBLIC_BASE_URL", "").rstrip("/")
JARVIS_PHONE_GREETING = os.getenv(
    "JARVIS_PHONE_GREETING",
    "Hello. This is JARVIS, an AI assistant. I am calling you because you asked me to. How can I help?",
)



def verify_twilio_signature(url: str, params: dict[str, str], signature: str) -> bool:
    """Validate the X-Twilio-Signature header for a webhook request."""
    if not TWILIO_AUTH_TOKEN or not signature:
        return False
    data = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(TWILIO_AUTH_TOKEN.encode(), data.encode(), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)

def configured() -> bool:
    return all(
        [TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, JARVIS_PUBLIC_BASE_URL]
    )


def _require_config() -> None:
    if not configured():
        raise HTTPException(
            503,
            "Phone gateway is not configured. Set Twilio credentials, TWILIO_FROM_NUMBER, "
            "and JARVIS_PUBLIC_BASE_URL.",
        )


async def create_call(to_number: str) -> dict:
    """Start an outbound PSTN call using Twilio's Calls API."""
    _require_config()
    if not to_number.startswith("+"):
        raise HTTPException(400, "Use E.164 format, for example +9198XXXXXXXX.")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    data = {
        "To": to_number,
        "From": TWILIO_FROM_NUMBER,
        "Url": f"{JARVIS_PUBLIC_BASE_URL}/phone/twiml/start",
        "Method": "POST",
        "StatusCallback": f"{JARVIS_PUBLIC_BASE_URL}/phone/status",
        "StatusCallbackMethod": "POST",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, data=data, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
    if r.status_code >= 400:
        raise HTTPException(r.status_code, f"Twilio call creation failed: {r.text[:500]}")
    return r.json()


def _say(text: str, voice: str = "Polly.Aditi", language: str = "en-IN") -> str:
    # Twilio Polly voice names may vary by account/region; fallback is handled
    # by Twilio if this voice is unavailable.
    safe = html.escape(text[:4000])
    return f'<Say voice="{voice}" language="{language}">{safe}</Say>'


def start_twiml() -> Response:
    """Initial call greeting and speech capture."""
    greeting = html.escape(JARVIS_PHONE_GREETING)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Aditi" language="en-IN">{greeting}</Say>
  <Gather input="speech" action="{JARVIS_PUBLIC_BASE_URL}/phone/twiml/turn"
          method="POST" speechTimeout="auto" language="en-IN" timeout="6">
    <Say voice="Polly.Aditi" language="en-IN">I am listening.</Say>
  </Gather>
  <Say voice="Polly.Aditi" language="en-IN">I did not hear anything. Goodbye.</Say>
  <Hangup/>
</Response>"""
    return Response(content=xml, media_type="application/xml")


async def turn_twiml(speech: str, call_sid: str, ai_answer) -> Response:
    """Generate the next conversational turn.

    ai_answer is injected from app.ai.answer so this module stays provider-focused.
    """
    if not speech.strip():
        reply = "I didn't catch that. Please say that again."
    else:
        try:
            reply = await ai_answer(speech.strip(), {"phone_call_sid": call_sid})
        except Exception:
            reply = "I had a problem processing that request. Please try again."

    safe = html.escape(str(reply)[:4000])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Aditi" language="en-IN">{safe}</Say>
  <Gather input="speech" action="{JARVIS_PUBLIC_BASE_URL}/phone/twiml/turn"
          method="POST" speechTimeout="auto" language="en-IN" timeout="6">
    <Say voice="Polly.Aditi" language="en-IN">Go ahead.</Say>
  </Gather>
  <Say voice="Polly.Aditi" language="en-IN">I will end the call now. Goodbye.</Say>
  <Hangup/>
</Response>"""
    return Response(content=xml, media_type="application/xml")


def status(payload: dict) -> dict:
    """Return a small normalized status object without persisting provider secrets."""
    return {
        "call_sid": payload.get("CallSid"),
        "status": payload.get("CallStatus"),
        "duration": payload.get("CallDuration"),
        "from": payload.get("From"),
        "to": payload.get("To"),
    }
