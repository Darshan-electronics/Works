"""Realtime Twilio <-> ElevenLabs <-> JARVIS voice bridge.

Twilio sends 8 kHz μ-law audio. ElevenLabs realtime STT accepts ulaw_8000,
and ElevenLabs dialogue streaming can return ulaw_8000, so the bridge avoids
a lossy server-side audio conversion step.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from typing import Awaitable, Callable

import websockets

ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVEN_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVEN_TTS_MODEL = os.getenv("ELEVENLABS_REALTIME_TTS_MODEL", "eleven_v3_conversational")
ELEVEN_STT_MODEL = os.getenv("ELEVENLABS_REALTIME_STT_MODEL", "scribe_v2_realtime")


async def run_call_bridge(
    twilio_ws,
    ai_answer: Callable[[str, dict], Awaitable[str]],
    call_sid: str = "",
) -> None:
    if not ELEVEN_KEY or not ELEVEN_VOICE_ID:
        await twilio_ws.close(code=1011, reason="ElevenLabs voice is not configured")
        return

    stt_url = (
        "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
        f"?model_id={ELEVEN_STT_MODEL}&audio_format=ulaw_8000"
        "&commit_strategy=vad&keepalive_interval_ms=1000"
    )
    tts_url = (
        "wss://api.elevenlabs.io/v1/text-to-dialogue/stream-input"
        f"?model_id={ELEVEN_TTS_MODEL}&output_format=ulaw_8000"
    )

    async with websockets.connect(stt_url, max_size=8 * 1024 * 1024) as stt,                websockets.connect(tts_url, max_size=8 * 1024 * 1024) as tts:

        await stt.send(json.dumps({
            "message_type": "input_audio_chunk",
            "audio_base_64": "",
            "commit": False,
            "sample_rate": 8000,
            "language_code": "en",
            "xi_api_key": ELEVEN_KEY,
        }))
        await stt.send(json.dumps({
            "config": {
                "audio_format": "ulaw_8000",
                "sample_rate": 8000,
                "language_code": "en",
                "model_id": ELEVEN_STT_MODEL,
            }
        }))
        await tts.send(json.dumps({
            "voices": [ELEVEN_VOICE_ID],
            "xi_api_key": ELEVEN_KEY,
            "language_code": "en",
        }))

        stream_sid = None
        response_lock = asyncio.Lock()

        async def send_tts(text: str) -> None:
            async with response_lock:
                await tts.send(json.dumps({
                    "inputs": [{
                        "text": text,
                        "voice_id": ELEVEN_VOICE_ID,
                        "new_turn": True,
                    }],
                    "flush": True,
                }))

        async def twilio_to_stt() -> None:
            nonlocal stream_sid
            async for raw in twilio_ws.iter_text():
                event = json.loads(raw)
                kind = event.get("event")
                if kind == "start":
                    stream_sid = event.get("start", {}).get("streamSid") or event.get("streamSid")
                elif kind == "media":
                    payload = event.get("media", {}).get("payload")
                    if payload:
                        await stt.send(json.dumps({
                            "message_type": "input_audio_chunk",
                            "audio_base_64": payload,
                            "commit": False,
                        }))
                elif kind == "stop":
                    break

        async def stt_to_tts() -> None:
            async for raw in stt:
                event = json.loads(raw)
                kind = event.get("message_type", "")
                if kind == "partial_transcript":
                    # Clear buffered JARVIS audio when the caller starts speaking.
                    if stream_sid and event.get("text", "").strip():
                        await twilio_ws.send_text(json.dumps({
                            "event": "clear",
                            "streamSid": stream_sid,
                        }))
                elif kind == "committed_transcript":
                    text = event.get("text", "").strip()
                    if not text:
                        continue
                    try:
                        reply = await ai_answer(
                            text,
                            {"phone_call_sid": call_sid, "channel": "realtime_phone"},
                        )
                    except Exception:
                        reply = "I encountered an internal problem. Please try again."
                    await send_tts(str(reply)[:4000])

        async def tts_to_twilio() -> None:
            async for raw in tts:
                event = json.loads(raw)
                audio = event.get("audio")
                if audio and stream_sid:
                    await twilio_ws.send_text(json.dumps({
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {"payload": audio},
                    }))

        tasks = [
            asyncio.create_task(twilio_to_stt()),
            asyncio.create_task(stt_to_tts()),
            asyncio.create_task(tts_to_twilio()),
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            if task.exception():
                raise task.exception()
