"""Voice providers. clip=false must never shorten text (walkthrough regression)."""

from __future__ import annotations

import base64
import hashlib
from collections import OrderedDict
from typing import Any

import httpx

from .config import settings

LEGACY_CLIP_CHARS = 520

# Server-side narration cache: identical text never re-bills ElevenLabs.
# Safe because the Modal API is pinned to one container.
_TTS_CACHE: "OrderedDict[str, dict]" = OrderedDict()
_TTS_CACHE_MAX = 300


def _cache_key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _cache_get(text: str) -> dict | None:
    key = _cache_key(text)
    if key in _TTS_CACHE:
        _TTS_CACHE.move_to_end(key)
        return _TTS_CACHE[key]
    return None


def _cache_put(text: str, audio: dict) -> None:
    _TTS_CACHE[_cache_key(text)] = audio
    while len(_TTS_CACHE) > _TTS_CACHE_MAX:
        _TTS_CACHE.popitem(last=False)


def prepare_spoken_text(text: str, *, clip: bool = False, max_chars: int = LEGACY_CLIP_CHARS) -> str:
    raw = text or ""
    if clip:
        return raw[:max_chars]
    return raw


def tts_payload(
    text: str,
    *,
    provider: str = "auto",
    language: str = "en",
    clip: bool = False,
) -> dict[str, Any]:
    spoken = prepare_spoken_text(text, clip=clip)
    if not clip and spoken != (text or ""):
        raise RuntimeError("TTS clip=false truncated text")

    chosen = provider
    if provider in {"auto", "elevenlabs"} and settings.elevenlabs_api_key:
        chosen = "elevenlabs"
        cached = _cache_get(spoken)
        if cached is not None:
            audio = {**cached, "cached": True}
        else:
            audio = _elevenlabs(spoken)
            if audio.get("status") == "ok":
                _cache_put(spoken, audio)
    elif provider == "sarvam" and settings.sarvam_api_key:
        chosen = "sarvam"
        audio = {"status": "ok", "note": "Sarvam Indic TTS — preserve NVIDIA English terms.", "chars": len(spoken)}
    else:
        chosen = "browser"
        audio = {"status": "browser_fallback", "chars": len(spoken)}

    return {
        "provider": chosen,
        "language": language,
        "clip": clip,
        "spoken_text": spoken,
        "char_count": len(spoken),
        "source_char_count": len(text or ""),
        "truncated": len(spoken) < len(text or ""),
        "elevenlabs_voice_settings": {"stability": 0.55, "speed": 0.93} if chosen == "elevenlabs" else None,
        "audio": audio,
        "evidence_type": "TUTOR_INTERPRETATION",
    }


def _elevenlabs(text: str) -> dict[str, Any]:
    voice = settings.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    try:
        with httpx.Client(timeout=90) as client:
            r = client.post(
                url,
                headers={"xi-api-key": settings.elevenlabs_api_key, "Accept": "audio/mpeg"},
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.55, "similarity_boost": 0.7, "speed": 0.93},
                },
            )
        if r.status_code >= 400:
            return {"error": r.text[:300], "chars": len(text)}
        return {
            "status": "ok",
            "bytes": len(r.content),
            "content_type": "audio/mpeg",
            "chars": len(text),
            "audio_base64": base64.b64encode(r.content).decode("ascii"),
        }
    except Exception as exc:
        return {"error": str(exc)[:300], "chars": len(text)}


def voice_status() -> dict[str, Any]:
    return {
        "elevenlabs": "connected" if settings.elevenlabs_api_key else "not_configured",
        "sarvam": "connected" if settings.sarvam_api_key else "not_configured",
        "browser_fallback": "connected",
        "clip_default": False,
        "note": "Walkthroughs must call POST /voice/tts with clip=false.",
    }
