from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
os.environ["DATABASE_URL"] = "sqlite:///" + str(ROOT / "services" / "api" / "data" / "test.db")
os.environ["COURSE_MATERIALS_DIR"] = str(ROOT / "course-materials")
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "services" / "twin-engine"))

from app.main import app, ensure_ready  # noqa: E402

ensure_ready()
client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_providers_ask_which_api():
    r = client.get("/api/providers")
    assert r.status_code == 200
    body = r.json()
    assert "demo" in str(body).lower()
    assert "ask" in body


def test_dashboard_asks_which_api():
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert "API" in body["ask_api"]
    assert "diagnostic_complete" in body
    assert body["tutor_provider"] in {"demo", "openai", "nim", "huggingface"}


def test_second_touch_of_concept_survives_sqlite_datetimes():
    first = client.get("/api/concepts/late-fusion")
    assert first.status_code == 200
    second = client.get("/api/concepts/late-fusion")
    assert second.status_code == 200
    tutor = client.post(
        "/api/tutor",
        json={"message": "Explain late fusion vs intermediate concat on the colored cubes task.", "mode": "course", "provider": "demo"},
    )
    assert tutor.status_code == 200
    assert tutor.json()["text"]
    q = client.get("/api/diagnostic").json()["items"][0]
    attempt = client.post(f"/api/questions/{q['id']}/attempt", json={"response": "nope", "hints": 0})
    assert attempt.status_code == 200


def test_twin_requires_simulation_label():
    r = client.post("/api/twins/fusion-lab/run", json={"controls": {"architecture": "lidar", "dataset": "colored_cubes"}, "prediction": "LiDAR will overfit"})
    assert r.status_code == 200
    assert r.json()["evidence_type"] == "SIMULATED_RESULT"
    assert r.json()["state"]["evidence_type"] == "SIMULATED_RESULT"


def test_course_tutor_without_spans_phrase():
    r = client.post("/api/tutor", json={"message": "What is Grove PodGang scheduling?", "mode": "course", "provider": "demo"})
    assert r.status_code == 200
    text = r.json()["text"].lower()
    assert "not established" in text or "retrieved" in text or "course" in text


def test_nav_endpoints_exist():
    for path in [
        "/api/dashboard",
        "/api/concepts",
        "/api/notebooks",
        "/api/twins",
        "/api/assessment",
        "/api/integrity",
        "/api/diagnostic",
        "/api/misconceptions",
    ]:
        assert client.get(path).status_code == 200, path


def test_fusion_search_ranks_fusion_notebooks():
    r = client.get("/api/search", params={"q": "late fusion vs intermediate concat colored cubes"})
    assert r.status_code == 200
    blob = str(r.json()).lower()
    assert "02a" in blob or "01a" in blob
    assert blob.find("02a") < blob.find("00_jupyter") or "00_jupyter" not in blob[:800]
