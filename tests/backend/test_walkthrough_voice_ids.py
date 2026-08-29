from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("DATABASE_URL", "sqlite:///" + str(ROOT / "services" / "api" / "data" / "test.db"))
os.environ.setdefault("COURSE_MATERIALS_DIR", str(ROOT / "course-materials"))
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "services" / "twin-engine"))

from app.db import Base, Notebook, SourceArtifact, SourceSpan  # noqa: E402
from app.ids import artifact_uid, notebook_uid, span_uid  # noqa: E402
from app.ingest import ingest_all  # noqa: E402
from app.main import CORS_ORIGIN_REGEX, app, ensure_ready  # noqa: E402
from app.voice import LEGACY_CLIP_CHARS, prepare_spoken_text, tts_payload  # noqa: E402
from app.walkthrough import (  # noqa: E402
    FRAMES,
    GLOSSARY,
    JARGON_SIMPLE_BLOCKLIST,
    WALKTHROUGH_KINDS,
    build_walkthrough,
    humanize_title,
    speakable,
)
from fastapi.testclient import TestClient  # noqa: E402

ensure_ready()
client = TestClient(app)


def test_artifact_ids_are_sha1_not_random():
    a = artifact_uid("01a_Early_and_Late_Fusion.ipynb")
    b = artifact_uid("01a_Early_and_Late_Fusion.ipynb")
    assert a == b
    assert len(a) == 16
    assert a != artifact_uid("02a_Intermediate_Fusion.ipynb")
    assert notebook_uid("01a_Early_and_Late_Fusion.ipynb") == a


def test_span_ids_deterministic():
    art = artifact_uid("01a.ipynb")
    loc = {"file": "01a.ipynb", "cell_index": 3}
    assert span_uid(art, loc, "code", 3) == span_uid(art, loc, "code", 3)
    assert span_uid(art, loc, "code", 3) != span_uid(art, loc, "code", 4)


def _ingest_uids(db_path: Path) -> dict[str, str]:
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    ingest_all(session)
    arts = {a.filename: a.uid for a in session.query(SourceArtifact).all()}
    nbs = {n.slug: n.uid for n in session.query(Notebook).all()}
    spans = [s.uid for s in session.query(SourceSpan).all()]
    session.close()
    engine.dispose()
    return {"arts": arts, "nbs": nbs, "span0": spans[0] if spans else ""}


def test_ids_stable_across_two_fresh_dbs(tmp_path):
    a = _ingest_uids(tmp_path / "a.db")
    b = _ingest_uids(tmp_path / "b.db")
    assert a["arts"] == b["arts"]
    assert a["nbs"] == b["nbs"]
    assert a["span0"] == b["span0"]
    assert all(a["arts"].values())


def test_notebook_name_and_uid_lookup():
    listed = client.get("/api/notebooks")
    assert listed.status_code == 200
    rows = listed.json()
    assert rows
    first = rows[0]
    by_slug = client.get(f"/api/notebooks/{first['slug']}")
    by_file = client.get(f"/api/notebooks/{first['slug']}.ipynb")
    by_id = client.get(f"/api/notebooks/{first['id']}")
    assert by_slug.status_code == 200
    assert by_file.status_code == 200
    assert by_id.status_code == 200
    assert by_slug.json()["id"] == by_id.json()["id"] == first["id"]
    again = client.get(f"/api/notebooks/{first['id']}")
    assert again.json()["id"] == first["id"]


def test_unknown_notebook_explains_staleness():
    r = client.get("/api/notebooks/not-a-real-notebook-zzz")
    assert r.status_code == 404
    assert "stale" in r.json()["detail"].lower()


def test_walkthrough_default_is_simple():
    r = client.get("/api/notebooks/01a_Early_and_Late_Fusion.ipynb/walkthrough")
    assert r.status_code == 200
    body = r.json()
    assert body["depth"] == "simple"
    assert body["clip"] is False


def test_walkthrough_expert_and_simple_parity():
    simple = client.get("/api/notebooks/02a_Intermediate_Fusion/walkthrough", params={"depth": "simple"}).json()
    expert = client.get("/api/notebooks/02a_Intermediate_Fusion/walkthrough", params={"depth": "expert"}).json()
    assert [s["kind"] for s in simple["steps"]] == [s["kind"] for s in expert["steps"]]
    assert simple["steps"][1]["text"] != expert["steps"][1]["text"]


def test_tts_clip_false_never_truncates():
    long = "fusion " * 200
    assert len(long) > LEGACY_CLIP_CHARS
    assert prepare_spoken_text(long, clip=False) == long
    clipped = prepare_spoken_text(long, clip=True)
    assert len(clipped) == LEGACY_CLIP_CHARS
    payload = tts_payload(long, clip=False)
    assert payload["spoken_text"] == long
    assert payload["truncated"] is False
    r = client.post("/api/voice/tts", json={"text": long, "clip": False, "provider": "auto"})
    assert r.status_code == 200
    assert r.json()["spoken_text"] == long
    assert r.json()["char_count"] == len(long)


def test_voice_status():
    r = client.get("/api/voice/status")
    assert r.status_code == 200
    assert r.json()["browser_fallback"] == "connected"
    assert r.json()["clip_default"] is False


def test_cors_regex_allows_modal_and_localhost():
    assert re.fullmatch(CORS_ORIGIN_REGEX, "https://modality-twin-academy-web-dev.modal.run")
    assert re.fullmatch(CORS_ORIGIN_REGEX, "https://foo.modal.app")
    assert re.fullmatch(CORS_ORIGIN_REGEX, "http://localhost:3000")
    assert re.fullmatch(CORS_ORIGIN_REGEX, "http://127.0.0.1:3000")
    assert not re.fullmatch(CORS_ORIGIN_REGEX, "https://evil.example")


def test_setup_and_risks_and_lessons():
    assert client.get("/api/setup").status_code == 200
    assert client.get("/api/setup").json()["go_live"] is True
    risks = client.get("/api/risks").json()
    assert 15 <= len(risks) <= 25
    assert client.get("/api/lessons").status_code == 200
    assert client.get("/api/learning/reviews/due").status_code == 200


def test_tutor_session_sse():
    created = client.post("/api/tutor/sessions", json={"mode": "course", "provider": "demo"})
    assert created.status_code == 200
    sid = created.json()["id"]
    r = client.post(f"/api/tutor/sessions/{sid}/messages", json={"message": "What is late fusion?"})
    assert r.status_code == 200
    assert "data:" in r.text


def test_span_and_source_uid():
    sources = client.get("/api/sources").json()
    assert sources
    detail = client.get(f"/api/sources/{sources[0]['id']}")
    assert detail.status_code == 200
    spans = detail.json()["spans"]
    assert spans
    one = client.get(f"/api/spans/{spans[0]['id']}")
    assert one.status_code == 200
    assert one.json()["evidence_type"] == "COURSE_SOURCE"


def test_humanize_and_speakable():
    assert humanize_title("2.3.4.1 Intermediate fusion") == "Intermediate fusion"
    spoken = speakable("RGB → LiDAR = 3/4 path?.")
    assert "then" in spoken
    assert "equals" in spoken
    assert "of" in spoken
    assert "?." not in spoken


def test_every_frame_complete_and_covers_cells():
    for filename, frame in FRAMES.items():
        for key in ("hook", "business", "simple_model", "expert_model", "game_plan", "remember", "stages", "dives"):
            assert frame.get(key), f"{filename} missing {key}"
        assert frame["simple_model"] != frame["expert_model"]
        simple = build_walkthrough(filename, frame["n_cells"], "simple")
        expert = build_walkthrough(filename, frame["n_cells"], "expert")
        assert [s["kind"] for s in simple["steps"]] == [s["kind"] for s in expert["steps"]]
        kinds = [s["kind"] for s in simple["steps"]]
        assert kinds[0] == "hook"
        assert kinds[1] == "model"
        assert kinds[-1] == "remember"
        assert "game_plan" in kinds
        assert "stage" in kinds
        assert set(kinds) <= set(WALKTHROUGH_KINDS)
        assert set(simple["covered_cells"]) == set(range(frame["n_cells"]))
        blob = " ".join(s["text"] for s in simple["steps"]).lower()
        for word in JARGON_SIMPLE_BLOCKLIST:
            assert word not in blob, f"{filename} simple leaked {word}"
        for step in simple["steps"]:
            assert "?." not in step["text"]
            assert not re.match(r"^\d+(?:\.\d+)+\s+", step["title"])
            if step["kind"] == "stage":
                assert len(step["text"]) <= 620
        titles = [s["kind"] for s in simple["steps"] if s["kind"] in {"hook", "model", "game_plan", "remember"}]
        assert titles.count("hook") == 1
        assert titles.count("model") == 1
        for term, definition in GLOSSARY.items():
            marker = f"{term} ({definition})"
            assert blob.count(marker) <= 1


def test_concepts_have_analogy_and_three_depths():
    nodes = client.get("/api/concepts").json()["nodes"]
    assert len(nodes) >= 90
    for n in nodes:
        assert n["school"]
        assert n["engineer"]
        assert n["research"]
        assert n.get("analogy") is not None


def test_twin_suggestions_validated():
    twins = client.get("/api/twins").json()
    assert 8 <= len(twins) <= 12
    slugs = {t["slug"] for t in twins}
    assert "incident-diagnosis" in slugs
    assert "risk-radar" in slugs
    for t in twins:
        assert len(t["suggestions"]) >= 3


def test_prediction_endpoints():
    r = client.post("/api/twins/fusion-lab/predictions", json={"prediction": "concat beats lidar on cubes"})
    assert r.status_code == 200
    listed = client.get("/api/twins/fusion-lab/predictions")
    assert listed.status_code == 200
    assert listed.json()


def test_notebook_business_tab():
    nb = client.get("/api/notebooks/05_Assessment").json()
    assert nb["cells"][0]["tabs"]["business"]
    assert nb["cells"][0]["tabs"]["plain"]
    assert "never" in nb["execution_policy"].lower()


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/api/providers",
        "/api/dashboard",
        "/api/concepts",
        "/api/notebooks",
        "/api/twins",
        "/api/assessment",
        "/api/integrity",
        "/api/diagnostic",
        "/api/misconceptions",
        "/api/progress",
        "/api/review",
        "/api/lessons",
        "/api/risks",
        "/api/setup",
        "/api/voice/status",
        "/api/learning/reviews/due",
        "/api/learning/mastery",
        "/api/learning/diagnostics",
        "/api/experiments",
        "/api/search?q=fusion",
        "/api/sources",
        "/api/questions",
        "/api/cost",
        "/api/notes",
        "/api/bookmarks",
        "/api/twins/fusion-lab",
        "/api/twins/incident-diagnosis",
        "/api/twins/risk-radar",
        "/api/concepts/late-fusion",
        "/api/lessons/late-fusion",
        "/api/notebooks/00_jupyterlab",
        "/api/notebooks/01a_Early_and_Late_Fusion",
        "/api/notebooks/01b_Exploring_Modalities",
        "/api/notebooks/02a_Intermediate_Fusion",
        "/api/notebooks/02b_Contrastive_Pretraining",
        "/api/notebooks/03a_Projection",
        "/api/notebooks/03b_OCR_Pipelines",
        "/api/notebooks/04a_VSS",
        "/api/notebooks/04b_VSS_GraphRAG",
        "/api/notebooks/05_Assessment",
    ],
)
def test_get_surface(path):
    assert client.get(path).status_code == 200, path


@pytest.mark.parametrize("filename", list(FRAMES))
@pytest.mark.parametrize("depth", ["simple", "expert"])
def test_walkthrough_http_every_notebook(filename, depth):
    r = client.get(f"/api/notebooks/{filename}/walkthrough", params={"depth": depth})
    assert r.status_code == 200
    body = r.json()
    assert body["depth"] == depth
    assert body["steps"]
    assert set(body["covered_cells"]) == set(range(body["n_cells"]))


@pytest.mark.parametrize("slug", ["lidar-geometry", "fusion-lab", "vss-pipeline", "graph-rag", "cilp-assessment"])
def test_twin_run_labeled_simulated(slug):
    r = client.post(f"/api/twins/{slug}/run", json={"controls": {}, "prediction": "hypothesis"})
    assert r.status_code == 200
    assert r.json()["evidence_type"] == "SIMULATED_RESULT"
