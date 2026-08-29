from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("DATABASE_URL", "sqlite:///" + str(ROOT / "services" / "api" / "data" / "test.db"))
os.environ.setdefault("COURSE_MATERIALS_DIR", str(ROOT / "course-materials"))
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "services" / "twin-engine"))

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Question  # noqa: E402
from app.main import _grade, app, ensure_ready  # noqa: E402
from app.voice import _TTS_CACHE, _cache_get, _cache_put  # noqa: E402

ensure_ready()
client = TestClient(app, raise_server_exceptions=False)


def _q(qtype: str, answer: str) -> Question:
    return Question(
        slug="t", qtype=qtype, bloom="recall", difficulty=1, concept_slug="lidar",
        prompt="p", options=[], answer=answer, explanation="e", source={},
    )


def test_free_text_grading_accepts_paraphrase():
    q = _q("short_answer", "Late fusion combines unimodal heads near the output into an ensemble-like MLP.")
    assert _grade(q, "late fusion is an ensemble that combines the unimodal heads at the output") is True
    assert _grade(q, "it uses kubernetes autoscaling") is False
    assert _grade(q, "no") is False


def test_mcq_grading_still_exact():
    q = _q("mcq", "240")
    assert _grade(q, "240") is True
    assert _grade(q, "120") is False


def test_unhandled_errors_return_explainable_json():
    from app import main as main_mod

    @main_mod.app.get("/api/_boom_test")
    def _boom():
        raise RuntimeError("synthetic failure")

    r = client.get("/api/_boom_test")
    assert r.status_code == 500
    body = r.json()
    assert "detail" in body
    assert "retry" in body["detail"].lower() or "Retry" in body["detail"]
    assert body["path"] == "/api/_boom_test"


def test_http_404_still_passes_through():
    r = client.get("/api/notebooks/definitely-not-real")
    assert r.status_code == 404
    assert "stale" in r.json()["detail"].lower()


def test_tts_cache_round_trip():
    _TTS_CACHE.clear()
    assert _cache_get("hello narration") is None
    _cache_put("hello narration", {"status": "ok", "bytes": 10})
    hit = _cache_get("hello narration")
    assert hit is not None and hit["bytes"] == 10
    for i in range(400):
        _cache_put(f"text-{i}", {"status": "ok", "bytes": i})
    assert len(_TTS_CACHE) <= 300


def test_setup_lists_disclaimer():
    r = client.get("/api/setup")
    assert "not affiliated" in r.json()["disclaimer"].lower()
