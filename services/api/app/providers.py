from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from .config import settings


@dataclass
class ProviderResult:
    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0
    ttft_ms: float | None = None
    tpot_ms: float | None = None
    tokens_per_sec: float | None = None
    evidence_type: str = "TUTOR_INTERPRETATION"
    raw: dict = field(default_factory=dict)
    error: str | None = None


class TutorModelProvider(ABC):
    name: str

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def complete(self, messages: list[dict], **kwargs: Any) -> ProviderResult: ...

    def health(self) -> dict:
        return {"name": self.name, "status": "connected" if self.available() else "offline"}


class DemoProvider(TutorModelProvider):
    name = "demo"

    def available(self) -> bool:
        return True

    def complete(self, messages: list[dict], **kwargs: Any) -> ProviderResult:
        t0 = time.perf_counter()
        context = kwargs.get("context") or []
        mode = kwargs.get("mode") or "course"
        question = messages[-1]["content"] if messages else ""
        if not context and mode == "course":
            text = (
                "This is not established by the supplied course material. "
                "Switch to Research Mode only if you explicitly want EXTERNAL_RESEARCH, "
                "or ask about fusion, LiDAR XYZA, CLIP/CILP, OCR, VSS, or Graph-RAG."
            )
            evidence = "COURSE_SOURCE"
        else:
            bullets = []
            for c in context[:4]:
                loc = c.get("locator") or {}
                bullets.append(
                    f"- ({loc.get('file', '?')} cell {loc.get('cell_index', loc.get('page', '?'))}) {c.get('text', '')[:420]}"
                )
            text = (
                "COURSE MODE — grounded in retrieved spans:\n"
                + "\n".join(bullets)
                + f"\n\nDirect answer: {kwargs.get('direct') or _heuristic_answer(question, context)}"
            )
            evidence = "TUTOR_INTERPRETATION"
        dt = (time.perf_counter() - t0) * 1000
        return ProviderResult(
            text=text,
            provider="demo",
            model="course-retriever-v1",
            input_tokens=sum(len(m["content"].split()) for m in messages),
            output_tokens=len(text.split()),
            latency_ms=dt,
            evidence_type=evidence,
        )


def _heuristic_answer(question: str, context: list[dict]) -> str:
    q = question.lower()
    if "xyza" in q or "azimuth" in q:
        return "x = d·sin(-az)·cos(-ze), y = d·cos(-az)·cos(-ze), z = d·sin(-ze), a = 1[d<50] (01a)."
    if "late fusion" in q:
        return "Late fusion combines unimodal heads near the output (01a/02a)."
    if "early fusion" in q:
        return "Early fusion concatenates RGB+XYZA channels into Net(8) (01a)."
    if "cilp" in q:
        return "CILP is Contrastive Image LiDAR Pre-training; freeze lidar_cnn; projector maps 200-d image embeddings into the CNN feature space (05)."
    if "chunk" in q and "vss" in q or "chunk_duration" in q:
        return "processed_frames = frames_per_chunk × video_length / chunk_size (04a). Shorter chunks → more frames, more detail, more latency."
    if "graph-rag" in q or "graph rag" in q:
        return "G-Extraction → G-Retriever (Cypher) → G-Generation. Live streams: Vector-RAG only (04b)."
    if context:
        return context[0].get("text", "")[:500]
    return "Ask a more specific question tied to a notebook concept."


class OpenAIProvider(TutorModelProvider):
    name = "openai"

    def available(self) -> bool:
        return bool(settings.openai_api_key)

    def complete(self, messages: list[dict], **kwargs: Any) -> ProviderResult:
        if not self.available():
            return ProviderResult(text="", provider="openai", model=settings.openai_model, error="OPENAI_API_KEY not configured")
        t0 = time.perf_counter()
        body = {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
        }
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        url = settings.openai_base_url.rstrip("/") + "/chat/completions"
        with httpx.Client(timeout=60) as client:
            r = client.post(url, headers=headers, json=body)
        latency = (time.perf_counter() - t0) * 1000
        if r.status_code >= 400:
            return ProviderResult(text="", provider="openai", model=settings.openai_model, latency_ms=latency, error=r.text[:500])
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        in_t = usage.get("prompt_tokens", 0)
        out_t = usage.get("completion_tokens", 0)
        tpot = latency / max(out_t, 1)
        return ProviderResult(
            text=text,
            provider="openai",
            model=settings.openai_model,
            input_tokens=in_t,
            output_tokens=out_t,
            latency_ms=latency,
            tpot_ms=tpot,
            tokens_per_sec=(out_t / (latency / 1000)) if latency else None,
            raw={"id": data.get("id")},
        )


class NvidiaNIMProvider(TutorModelProvider):
    name = "nim"

    def available(self) -> bool:
        return bool(settings.nim_base_url and settings.nvidia_api_key)

    def complete(self, messages: list[dict], **kwargs: Any) -> ProviderResult:
        if not self.available():
            return ProviderResult(text="", provider="nim", model=settings.nvidia_nim_model, error="NIM_BASE_URL / NVIDIA_API_KEY not configured")
        t0 = time.perf_counter()
        url = settings.nim_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.nvidia_api_key}", "Accept": "application/json"}
        body = {"model": settings.nvidia_nim_model, "messages": messages, "temperature": 0.2}
        with httpx.Client(timeout=90) as client:
            r = client.post(url, headers=headers, json=body)
        latency = (time.perf_counter() - t0) * 1000
        if r.status_code >= 400:
            return ProviderResult(text="", provider="nim", model=settings.nvidia_nim_model, latency_ms=latency, error=r.text[:500])
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        return ProviderResult(
            text=text,
            provider="nim",
            model=settings.nvidia_nim_model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency,
        )


class HuggingFaceProvider(TutorModelProvider):
    name = "huggingface"

    def available(self) -> bool:
        return bool(settings.hf_token)

    def complete(self, messages: list[dict], **kwargs: Any) -> ProviderResult:
        if not self.available():
            return ProviderResult(text="", provider="huggingface", model=settings.hf_model, error="HF_TOKEN not configured")
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        t0 = time.perf_counter()
        url = f"https://api-inference.huggingface.co/models/{settings.hf_model}"
        with httpx.Client(timeout=90) as client:
            r = client.post(url, headers={"Authorization": f"Bearer {settings.hf_token}"}, json={"inputs": prompt, "parameters": {"max_new_tokens": 400}})
        latency = (time.perf_counter() - t0) * 1000
        if r.status_code >= 400:
            return ProviderResult(text="", provider="huggingface", model=settings.hf_model, latency_ms=latency, error=r.text[:400])
        data = r.json()
        if isinstance(data, list) and data and "generated_text" in data[0]:
            text = data[0]["generated_text"]
        else:
            text = str(data)[:4000]
        return ProviderResult(text=text, provider="huggingface", model=settings.hf_model, latency_ms=latency, output_tokens=len(text.split()))


class PerplexityResearchProvider:
    name = "perplexity"

    def available(self) -> bool:
        return bool(settings.perplexity_api_key)

    def search(self, query: str) -> dict:
        if not self.available():
            return {"error": "PERPLEXITY_API_KEY not configured", "citations": []}
        headers = {"Authorization": f"Bearer {settings.perplexity_api_key}"}
        body = {
            "model": "sonar",
            "messages": [{"role": "user", "content": query}],
        }
        with httpx.Client(timeout=60) as client:
            r = client.post("https://api.perplexity.ai/chat/completions", headers=headers, json=body)
        if r.status_code >= 400:
            return {"error": r.text[:400], "citations": []}
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return {"text": text, "citations": data.get("citations") or [], "evidence_type": "EXTERNAL_RESEARCH"}


class VoiceProvider(ABC):
    name: str

    @abstractmethod
    def available(self) -> bool: ...


class ElevenLabsVoiceProvider(VoiceProvider):
    name = "elevenlabs"

    def available(self) -> bool:
        return bool(settings.elevenlabs_api_key)

    def tts(self, text: str) -> dict:
        if not self.available():
            return {"error": "ELEVENLABS_API_KEY not configured"}
        return {"status": "ok", "note": "Audio bytes streamed by /voice/tts when key present.", "chars": len(text)}


class SarvamVoiceProvider(VoiceProvider):
    name = "sarvam"

    def available(self) -> bool:
        return bool(settings.sarvam_api_key)

    def explain_indic(self, text: str, language: str) -> dict:
        if not self.available():
            return {"error": "SARVAM_API_KEY not configured — not required to start the app"}
        return {"language": language, "note": "Preserve NVIDIA English technical terms.", "text": text}


class OpenAIRealtimeVoiceProvider(VoiceProvider):
    name = "openai_realtime"

    def available(self) -> bool:
        return bool(settings.openai_api_key)

    def session_config(self) -> dict:
        return {"model": settings.openai_realtime_model, "modalities": ["audio", "text"], "barge_in": True}


PROVIDERS: dict[str, TutorModelProvider] = {
    "demo": DemoProvider(),
    "openai": OpenAIProvider(),
    "nim": NvidiaNIMProvider(),
    "huggingface": HuggingFaceProvider(),
}


def get_tutor_provider(name: str) -> TutorModelProvider:
    return PROVIDERS.get(name, PROVIDERS["demo"])


def provider_matrix() -> list[dict]:
    research = PerplexityResearchProvider()
    voices = [ElevenLabsVoiceProvider(), SarvamVoiceProvider(), OpenAIRealtimeVoiceProvider()]
    rows = [p.health() for p in PROVIDERS.values()]
    rows.append({"name": "perplexity", "status": "connected" if research.available() else "not_configured"})
    for v in voices:
        rows.append({"name": v.name, "status": "connected" if v.available() else "not_configured"})
    rows.append({"name": "omniverse", "status": "offline"})
    return rows
