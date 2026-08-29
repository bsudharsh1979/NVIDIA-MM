from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "twin-engine"))

from twin_engine import SCENARIOS, SUGGESTED_SCENARIOS, TwinState, run_scenario  # noqa: E402

from .config import settings
from .lookup import resolve_notebook, resolve_source, resolve_span
from .risks import RISKS
from .voice import tts_payload, voice_status
from .walkthrough import build_walkthrough
from .db import (
    Bookmark,
    Concept,
    ConceptEdge,
    DigitalTwin,
    EvidenceArtifact,
    Experiment,
    IntegrityFlag,
    LearnerPrediction,
    Lesson,
    MasteryState,
    Misconception,
    Note,
    Notebook,
    NotebookCell,
    ProviderSetting,
    ProviderTrace,
    Question,
    QuestionAttempt,
    ReviewItem,
    SourceArtifact,
    SourceSpan,
    TutorSession,
    TwinRun,
    User,
    get_session,
    init_db,
)
from .experiments import compare_experiments, explain_experiment, import_payload
from .ingest import CELL_TEACHING, NOTEBOOK_OVERVIEWS, hybrid_search
from .mastery import apply_event, explain_mastery, schedule_review
from .providers import PROVIDERS, get_tutor_provider, provider_matrix
from .seed import seed
from .tutor import grade_teachback, tutor_turn, why_wrong

CORS_ORIGIN_REGEX = r"https://.*\.(modal\.run|modal\.app)|https://.*\.vercel\.app|http://(localhost|127\.0\.0\.1):\d+"

app = FastAPI(title="Modality Twin Academy", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_LAST_TWIN: TwinState | None = None
_READY = False


def ensure_ready() -> None:
    global _READY
    if _READY:
        return
    init_db()
    seed()
    _READY = True


def db_dep():
    ensure_ready()
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def learner(session: Session) -> User:
    user = session.query(User).filter_by(handle="learner").one()
    return user


@app.on_event("startup")
def _startup():
    ensure_ready()


class ChatIn(BaseModel):
    message: str
    mode: str = "course"
    depth: str = "engineer"
    provider: str | None = None
    session_id: int | None = None


class AttemptIn(BaseModel):
    response: str
    hints: int = 0
    latency_ms: int = 0


class TwinIn(BaseModel):
    controls: dict[str, Any] = Field(default_factory=dict)
    prediction: str | None = None


class SettingsIn(BaseModel):
    tutor_provider: str = "demo"
    voice_provider: str = "off"
    research_provider: str = "off"
    depth: str = "engineer"
    course_mode: str = "course"


class NoteIn(BaseModel):
    target_type: str
    target_id: str
    body: str


class TeachIn(BaseModel):
    text: str
    concept_slug: str | None = None


@app.get("/health")
def health():
    return {"ok": True, "product": "Modality Twin Academy"}


@app.get("/api/providers")
def api_providers(session: Session = Depends(db_dep)):
    user = learner(session)
    ps = session.query(ProviderSetting).filter_by(user_id=user.id).one_or_none()
    return {
        "matrix": provider_matrix(),
        "selected": {
            "tutor_provider": (ps.tutor_provider if ps else "demo"),
            "voice_provider": (ps.voice_provider if ps else "off"),
            "research_provider": (ps.research_provider if ps else "off"),
            "depth": (ps.depth if ps else "engineer"),
            "course_mode": (ps.course_mode if ps else "course"),
        },
        "ask": "Choose a tutor API: Demo (offline), OpenAI, NVIDIA NIM, or Hugging Face. Voice and Perplexity are optional.",
    }


@app.put("/api/providers")
def api_providers_put(body: SettingsIn, session: Session = Depends(db_dep)):
    if body.tutor_provider not in {*"demo openai nim huggingface".split()}:
        raise HTTPException(400, "Unknown tutor provider")
    user = learner(session)
    ps = session.query(ProviderSetting).filter_by(user_id=user.id).one_or_none()
    if not ps:
        ps = ProviderSetting(user_id=user.id)
        session.add(ps)
    ps.tutor_provider = body.tutor_provider
    ps.voice_provider = body.voice_provider
    ps.research_provider = body.research_provider
    ps.depth = body.depth
    ps.course_mode = body.course_mode
    session.commit()
    prov = get_tutor_provider(ps.tutor_provider)
    if ps.tutor_provider != "demo" and not prov.available():
        return {"ok": True, "warning": f"{ps.tutor_provider} selected but not configured — tutor will disclose fallback to demo.", "selected": body.model_dump()}
    return {"ok": True, "selected": body.model_dump()}


@app.get("/api/dashboard")
def dashboard(session: Session = Depends(db_dep)):
    user = learner(session)
    states = session.query(MasteryState).filter_by(user_id=user.id).all()
    due = session.query(ReviewItem).filter(ReviewItem.user_id == user.id).count()
    ranked = sorted(states, key=lambda s: s.score)
    weakest = [{"slug": s.concept_slug, "score": s.score} for s in ranked[:8]]
    strongest = [{"slug": s.concept_slug, "score": s.score} for s in ranked[-8:][::-1]]
    overall = sum(s.score for s in states) / max(len(states), 1)
    misconceptions = sum(len(s.misconception_tags or []) for s in states)
    resume = user.last_resume_json or {
        "text": "Last time you were comparing early vs intermediate fusion on colored cubes. Decode analog: LiDAR lacked the color identity signal."
    }
    plan = _thirty_min_plan(weakest)
    ps = session.query(ProviderSetting).filter_by(user_id=user.id).one_or_none()
    attempts = session.query(QuestionAttempt).filter_by(user_id=user.id).count()
    return {
        "overall_mastery": round(overall, 3),
        "heatmap": [{"slug": s.concept_slug, "score": round(s.score, 3), "tags": s.misconception_tags} for s in states],
        "reviews_due": due,
        "weakest": weakest,
        "strongest": strongest,
        "misconception_count": misconceptions,
        "assessment_readiness": round(min(1.0, overall * 1.1), 3),
        "resume": resume,
        "plan": plan,
        "what_i_know": strongest[:3],
        "what_i_forget": weakest[:3],
        "next_learn": plan[0] if plan else None,
        "blocking_misconception": _first_misconception(states),
        "notebook_revisit": "02a_Intermediate_Fusion.ipynb" if overall < 0.5 else "04a_VSS.ipynb",
        "twin_run": "fusion-lab" if overall < 0.45 else "vss-pipeline",
        "diagnostic_complete": attempts >= 8,
        "attempt_count": attempts,
        "tutor_provider": ps.tutor_provider if ps else "demo",
        "ask_api": "Which API do you want? Demo (offline), OpenAI, NVIDIA NIM, or Hugging Face.",
    }


def _first_misconception(states) -> str | None:
    for s in states:
        if s.misconception_tags:
            return s.misconception_tags[0]
    return None


def _thirty_min_plan(weakest):
    steps = []
    if weakest:
        steps.append({"minutes": 8, "action": f"Active lesson: {weakest[0]['slug']}", "href": f"/learn/{weakest[0]['slug']}"})
    steps.append({"minutes": 7, "action": "LiDAR geometry twin — predict XYZ before revealing", "href": "/twins/lidar-geometry"})
    steps.append({"minutes": 8, "action": "Notebook studio: fusion or VSS cell walkthrough", "href": "/notebooks"})
    steps.append({"minutes": 7, "action": "Practice + FSRS reviews due today", "href": "/review"})
    return steps


@app.get("/api/concepts")
def concepts(session: Session = Depends(db_dep)):
    nodes = session.query(Concept).all()
    edges = session.query(ConceptEdge).all()
    return {
        "nodes": [
            {
                "slug": n.slug,
                "name": n.name,
                "cluster": n.cluster,
                "school": n.school,
                "engineer": n.engineer,
                "research": n.research,
                "analogy": n.analogy,
                "twin_id": n.twin_id,
                "source": n.source,
                "misconceptions": n.common_misconceptions,
            }
            for n in nodes
        ],
        "edges": [{"src": e.src, "dst": e.dst, "relation": e.relation, "note": e.note} for e in edges],
    }


@app.get("/api/concepts/{slug}")
def concept_detail(slug: str, session: Session = Depends(db_dep)):
    n = session.query(Concept).filter_by(slug=slug).one_or_none()
    if not n:
        raise HTTPException(404)
    user = learner(session)
    mastery = session.query(MasteryState).filter_by(user_id=user.id, concept_slug=slug).one_or_none()
    if mastery:
        apply_event(mastery, "viewed", True, 0.2)
        session.commit()
    prereq = session.query(ConceptEdge).filter_by(dst=slug).all()
    related = session.query(ConceptEdge).filter((ConceptEdge.src == slug) | (ConceptEdge.dst == slug)).all()
    return {
        "slug": n.slug,
        "name": n.name,
        "cluster": n.cluster,
        "school": n.school,
        "engineer": n.engineer,
        "research": n.research,
        "analogy": n.analogy,
        "twin_id": n.twin_id,
        "source": n.source,
        "misconceptions": n.common_misconceptions,
        "mastery": explain_mastery(mastery) if mastery else None,
        "prerequisites": [e.src for e in prereq if e.relation == "PREREQUISITE_OF"],
        "related": [{"src": e.src, "dst": e.dst, "relation": e.relation} for e in related],
        "quiz_href": f"/practice?concept={slug}",
        "twin_href": f"/twins/{n.twin_id}" if n.twin_id else None,
    }


@app.get("/api/notebooks")
def notebooks(session: Session = Depends(db_dep)):
    nbs = session.query(Notebook).order_by(Notebook.order_index).all()
    return [
        {
            "id": n.uid or n.slug,
            "slug": n.slug,
            "purpose": n.purpose,
            "why_it_matters": n.why_it_matters,
            "expected_outcome": n.expected_outcome,
            "order": n.order_index,
            "overview": NOTEBOOK_OVERVIEWS.get(n.slug + ".ipynb") or NOTEBOOK_OVERVIEWS.get(n.slug),
        }
        for n in nbs
    ]


@app.get("/api/notebooks/{key}")
def notebook_detail(key: str, session: Session = Depends(db_dep)):
    nb = resolve_notebook(session, key)
    cells = session.query(NotebookCell).filter_by(notebook_id=nb.id).order_by(NotebookCell.cell_index).all()
    artifact = session.get(SourceArtifact, nb.artifact_id)
    filename = artifact.filename if artifact else (nb.slug if nb.slug.endswith(".ipynb") else f"{nb.slug}.ipynb")
    flow = [c.heading for c in cells if c.heading]
    uniq_flow = []
    for h in flow:
        if h not in uniq_flow:
            uniq_flow.append(h)
    return {
        "id": nb.uid or nb.slug,
        "slug": nb.slug,
        "filename": filename,
        "purpose": nb.purpose,
        "why_it_matters": nb.why_it_matters,
        "expected_outcome": nb.expected_outcome,
        "flow": uniq_flow,
        "disclaimer": "Not affiliated with or endorsed by NVIDIA. Notebook code is DATA — parsed and displayed, never executed.",
        "execution_policy": "Notebook code is educational content. The academy never auto-executes shell, kubectl, helm, docker, or Python from cells.",
        "cells": [
            {
                "index": c.cell_index,
                "type": c.cell_type,
                "heading": c.heading,
                "markdown": c.markdown,
                "code": c.code,
                "stored_output": c.stored_output,
                "output_class": "COURSE_SOURCE" if c.stored_output else "EXPECTED_RESULT",
                "execution_count": c.execution_count,
                "dangerous": c.dangerous,
                "commands": c.commands,
                "extras": c.extras,
                "never_execute": bool(c.dangerous),
                "locator": {"source_type": "notebook", "file": filename, "cell_index": c.cell_index},
                "tabs": {
                    "plain": _plain_english(c),
                    "plain_english": _plain_english(c),
                    "line_by_line": (c.code or c.markdown).splitlines()[:80],
                    "why": CELL_TEACHING["why"],
                    "business": CELL_TEACHING["business"],
                    "should": "See markdown near this cell; stored outputs are absent in this clone unless present in the ipynb.",
                    "what_should_happen": "See markdown near this cell; stored outputs are absent in this clone unless present in the ipynb.",
                    "verify": CELL_TEACHING["verify"],
                    "how_to_verify": CELL_TEACHING["verify"],
                    "failure": CELL_TEACHING["failure"],
                    "common_failure": CELL_TEACHING["failure"],
                    "try_modifying": CELL_TEACHING["modify"],
                },
            }
            for c in cells
        ],
    }


@app.get("/api/notebooks/{key}/walkthrough")
def notebook_walkthrough(key: str, depth: str = "simple", session: Session = Depends(db_dep)):
    nb = resolve_notebook(session, key)
    n_cells = session.query(NotebookCell).filter_by(notebook_id=nb.id).count()
    artifact = session.get(SourceArtifact, nb.artifact_id)
    filename = artifact.filename if artifact else f"{nb.slug}.ipynb"
    return build_walkthrough(filename, n_cells, depth)


def _plain_english(cell: NotebookCell) -> str:
    if cell.markdown:
        return cell.markdown[:600]
    code = cell.code or ""
    if "FIXME" in code:
        return "Exercise cell — replace FIXME using the nearby solution cell; do not skip the prediction step."
    if cell.dangerous:
        return "This cell would talk to an external cluster or shell in the DLI classroom. Here it is shown, not executed."
    return "Executable illustration of the surrounding markdown."


@app.get("/api/sources")
def sources(session: Session = Depends(db_dep)):
    arts = session.query(SourceArtifact).all()
    return [
        {"id": a.uid or str(a.id), "numeric_id": a.id, "type": a.source_type, "file": a.filename, "title": a.title, "extra": a.extra}
        for a in arts
    ]


@app.get("/api/sources/{key}")
def source_detail(key: str, session: Session = Depends(db_dep)):
    art = resolve_source(session, key)
    spans = session.query(SourceSpan).filter_by(artifact_id=art.id).all()
    return {
        "id": art.uid or str(art.id),
        "type": art.source_type,
        "file": art.filename,
        "title": art.title,
        "extra": art.extra,
        "spans": [
            {
                "id": s.uid or str(s.id),
                "title": s.title,
                "locator": s.locator,
                "text": (s.text or s.code)[:2000],
                "heading": s.heading,
            }
            for s in spans
        ],
    }


@app.get("/api/spans/{key}")
def span_detail(key: str, session: Session = Depends(db_dep)):
    span = resolve_span(session, key)
    art = session.get(SourceArtifact, span.artifact_id)
    return {
        "id": span.uid or str(span.id),
        "artifact_id": art.uid if art else None,
        "file": art.filename if art else None,
        "title": span.title,
        "locator": span.locator,
        "heading": span.heading,
        "text": (span.text or span.code)[:8000],
        "evidence_type": "COURSE_SOURCE",
    }


@app.get("/api/search")
def search(q: str, session: Session = Depends(db_dep)):
    return hybrid_search(session, q, k=10)


@app.post("/api/tutor")
def api_tutor(body: ChatIn, session: Session = Depends(db_dep)):
    user = learner(session)
    ps = session.query(ProviderSetting).filter_by(user_id=user.id).one_or_none()
    provider = body.provider or (ps.tutor_provider if ps else "demo")
    mode = body.mode or (ps.course_mode if ps else "course")
    depth = body.depth or (ps.depth if ps else "engineer")
    result = tutor_turn(
        session,
        user.id,
        body.message,
        mode=mode,
        depth=depth,
        provider_name=provider,
        tutor_session_id=body.session_id,
    )
    session.add(
        ProviderTrace(
            provider=result["telemetry"]["provider"],
            model=result["telemetry"].get("model") or "",
            feature="tutor",
            input_tokens=result["telemetry"].get("input_tokens") or 0,
            output_tokens=result["telemetry"].get("output_tokens") or 0,
            latency_ms=result["telemetry"].get("latency_ms") or 0,
            ttft_ms=result["telemetry"].get("ttft_ms"),
            tpot_ms=result["telemetry"].get("tpot_ms"),
        )
    )
    user.last_resume_json = {"text": f"You asked the tutor: {body.message[:180]}", "href": "/tutor"}
    session.commit()
    return result


@app.post("/api/teachback")
def api_teachback(body: TeachIn, session: Session = Depends(db_dep)):
    user = learner(session)
    concepts = [body.concept_slug] if body.concept_slug else []
    result = grade_teachback(body.text, concepts)
    if body.concept_slug:
        st = session.query(MasteryState).filter_by(user_id=user.id, concept_slug=body.concept_slug).one_or_none()
        if st:
            apply_event(st, "teachback", result["quality"] >= 0.6, result["quality"])
            session.commit()
    return result


@app.get("/api/twins")
def twins(session: Session = Depends(db_dep)):
    rows = session.query(DigitalTwin).all()
    return [
        {
            "slug": t.slug,
            "id": t.slug,
            "title": t.title,
            "summary": t.summary,
            "controls": t.controls,
            "suggestions": SUGGESTED_SCENARIOS.get(t.slug, []),
        }
        for t in rows
    ]


@app.get("/api/twins/{slug}")
def twin_detail(slug: str, session: Session = Depends(db_dep)):
    t = session.query(DigitalTwin).filter_by(slug=slug).one_or_none()
    if not t or slug not in SCENARIOS:
        raise HTTPException(404, "Unknown twin")
    return {
        "slug": t.slug,
        "id": t.slug,
        "title": t.title,
        "summary": t.summary,
        "controls": t.controls,
        "suggestions": SUGGESTED_SCENARIOS.get(t.slug, []),
        "predict_prompt": "Write what you expect the key metric to do before the twin runs. Outcomes are SIMULATED_RESULT.",
        "withholds_truth": slug == "incident-diagnosis",
    }


@app.post("/api/twins/{slug}/run")
def twin_run(slug: str, body: TwinIn, session: Session = Depends(db_dep)):
    global _LAST_TWIN
    if slug not in SCENARIOS:
        raise HTTPException(404, "Unknown twin")
    user = learner(session)
    if body.prediction:
        session.add(
            LearnerPrediction(
                user_id=user.id,
                twin_id=slug,
                prompt="pre-run prediction",
                prediction=body.prediction,
                actual={},
                evidence_type="SIMULATED_RESULT",
            )
        )
    state = run_scenario(slug, body.controls)
    _LAST_TWIN = state
    session.add(TwinRun(user_id=user.id, twin_slug=slug, state=state.model_dump()))
    session.add(
        EvidenceArtifact(
            evidence_type="SIMULATED_RESULT",
            label=f"{slug} run",
            payload=state.metrics,
            source={"twin": slug},
        )
    )
    user.last_resume_json = {"text": f"You ran the {slug} twin.", "href": f"/twins/{slug}"}
    session.commit()
    comparison = None
    if body.prediction:
        comparison = {
            "prediction": body.prediction,
            "simulated": state.metrics,
            "evidence_type": "SIMULATED_RESULT",
            "prompt": "Why did the simulated result differ from your prediction?",
        }
    return {"state": state.model_dump(), "prediction_comparison": comparison, "evidence_type": "SIMULATED_RESULT"}


@app.get("/api/twins/{slug}/state")
def twin_state(slug: str):
    if _LAST_TWIN and _LAST_TWIN.scenario == slug:
        return _LAST_TWIN.model_dump()
    return run_scenario(slug, {}).model_dump()


@app.websocket("/ws/twin")
async def ws_twin(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            scenario = data.get("scenario") or "fusion-lab"
            state = run_scenario(scenario, data.get("controls") or {})
            await ws.send_json({"channel": "omniverse", "state": state.model_dump()})
    except Exception:
        await ws.close()


@app.get("/api/questions")
def questions(concept: str | None = None, bloom: str | None = None, session: Session = Depends(db_dep)):
    q = session.query(Question)
    if concept:
        q = q.filter_by(concept_slug=concept)
    if bloom:
        q = q.filter_by(bloom=bloom)
    rows = q.limit(40).all()
    return [_public_question(r) for r in rows]


def _public_question(r: Question) -> dict:
    return {
        "id": r.id,
        "slug": r.slug,
        "qtype": r.qtype,
        "bloom": r.bloom,
        "difficulty": r.difficulty,
        "concept_slug": r.concept_slug,
        "prompt": r.prompt,
        "options": r.options,
        "source": r.source,
        "has_hidden_answer": True,
    }


@app.post("/api/questions/{qid}/attempt")
def attempt(qid: int, body: AttemptIn, session: Session = Depends(db_dep)):
    q = session.get(Question, qid)
    if not q:
        raise HTTPException(404)
    user = learner(session)
    correct = _grade(q, body.response)
    fb = None if correct else why_wrong(body.response, {"misconception_slug": q.misconception_slug, "explanation": q.explanation, "source": q.source})
    session.add(
        QuestionAttempt(
            user_id=user.id,
            question_id=q.id,
            response=body.response,
            correct=correct,
            hints=body.hints,
            latency_ms=body.latency_ms,
            feedback=fb or {},
        )
    )
    st = session.query(MasteryState).filter_by(user_id=user.id, concept_slug=q.concept_slug).one_or_none()
    if st:
        kind = "recall" if q.bloom in {"recall"} else "diagnose" if q.bloom == "diagnose" else "apply"
        apply_event(st, kind if kind in {"recall", "diagnose", "apply", "explain"} else "recall", correct, 0.9 if correct else 0.2, q.misconception_slug or None)
        if body.hints:
            st.hints_used += body.hints
    if not correct:
        schedule_review(session, user.id, q.concept_slug, q.id, "wrong")
    session.commit()
    return {
        "correct": correct,
        "answer": q.answer if correct or body.hints >= 2 else None,
        "explanation": q.explanation if correct or body.hints >= 1 else None,
        "why_wrong": fb,
        "source": q.source,
        "socratic": None if correct else "Which distinction did you skip? Retry before the full answer is shown.",
    }


def _grade(q: Question, response: str) -> bool:
    gold = (q.answer or "").strip().lower()
    got = (response or "").strip().lower()
    if q.qtype in {"multiple_select", "sequence"}:
        def norm(s: str) -> list[str]:
            return [p.strip() for p in s.replace(",", "|").split("|") if p.strip()]
        return sorted(norm(gold)) == sorted(norm(got)) or gold == got
    if gold == got:
        return True
    if gold in got or got in gold:
        return len(got) > 8
    return False


@app.get("/api/diagnostic")
def diagnostic(session: Session = Depends(db_dep)):
    topics = [
        "lidar-xyza",
        "late-fusion",
        "early-fusion",
        "colored-cubes-task",
        "clip-style",
        "cross-modal-projection",
        "ocr",
        "vss-chunk-duration",
        "graph-rag",
        "cilp",
    ]
    items = []
    for slug in topics:
        q = session.query(Question).filter_by(concept_slug=slug, qtype="mcq").first()
        if q:
            items.append(_public_question(q))
    return {"items": items, "note": "Adaptive: later items get harder if you are succeeding."}


@app.get("/api/lessons")
def lessons(session: Session = Depends(db_dep)):
    rows = session.query(Lesson).all()
    return [{"slug": r.slug, "title": r.title, "concept_slug": r.concept_slug, "twin_id": r.twin_id} for r in rows]


@app.get("/api/lessons/{slug}")
def lesson(slug: str, session: Session = Depends(db_dep)):
    row = session.query(Lesson).filter_by(slug=slug).one_or_none()
    if not row:
        row = session.query(Lesson).filter_by(concept_slug=slug).first()
    if not row:
        raise HTTPException(404)
    return {"slug": row.slug, "title": row.title, "concept_slug": row.concept_slug, "steps": row.steps, "twin_id": row.twin_id}


@app.get("/api/review")
def review(session: Session = Depends(db_dep)):
    user = learner(session)
    items = session.query(ReviewItem).filter_by(user_id=user.id).all()
    return [{"id": i.id, "concept": i.concept_slug, "due": i.due.isoformat(), "reason": i.reason, "question_id": i.question_id} for i in items]


@app.get("/api/progress")
def progress(session: Session = Depends(db_dep)):
    user = learner(session)
    states = session.query(MasteryState).filter_by(user_id=user.id).all()
    traces = session.query(ProviderTrace).all()
    cost = sum(t.cost_usd for t in traces)
    return {
        "mastery": [explain_mastery(s) | {"slug": s.concept_slug, "next_review": s.next_review.isoformat() if s.next_review else None} for s in states],
        "usage": {
            "calls": len(traces),
            "input_tokens": sum(t.input_tokens for t in traces),
            "output_tokens": sum(t.output_tokens for t in traces),
            "cost_usd": cost,
            "budget_usd": settings.monthly_budget_usd,
        },
        "resume": user.last_resume_json,
    }


@app.post("/api/experiments/import")
async def exp_import(
    kind: str = Form("json"),
    name: str = Form("imported-run"),
    file: UploadFile | None = File(None),
    raw_text: str = Form(""),
    session: Session = Depends(db_dep),
):
    user = learner(session)
    raw = raw_text
    filename = ""
    if file:
        filename = file.filename or "upload"
        raw = (await file.read()).decode("utf-8", errors="replace")
    payload = import_payload(kind, name, user.id, raw, filename)
    exp = Experiment(
        user_id=user.id,
        name=name,
        kind=kind,
        metadata_json={"filename": filename},
        evidence_type="ACTUAL_RUN",
        raw_ref=filename,
    )
    session.add(exp)
    session.flush()
    from .db import BenchmarkRun

    session.add(BenchmarkRun(experiment_id=exp.id, metrics=payload["metrics"], raw=payload["parsed"] if isinstance(payload["parsed"], dict) else {"wrapped": True}))
    session.add(EvidenceArtifact(evidence_type="ACTUAL_RUN", label=name, payload=payload["metrics"], source={"file": filename}))
    session.commit()
    return {"id": exp.id, **payload, "explainer": explain_experiment(payload)}


@app.get("/api/experiments")
def exp_list(session: Session = Depends(db_dep)):
    user = learner(session)
    rows = session.query(Experiment).filter_by(user_id=user.id).all()
    return [{"id": r.id, "name": r.name, "kind": r.kind, "evidence_type": r.evidence_type, "metadata": r.metadata_json} for r in rows]


class CompareIn(BaseModel):
    a: dict
    b: dict


@app.post("/api/experiments/compare")
def exp_compare(body: CompareIn):
    cmp_ = compare_experiments(body.a, body.b)
    return {**cmp_, "explainer": explain_experiment({**cmp_, "metrics": body.a.get("metrics") or {}})}


@app.get("/api/integrity")
def integrity(session: Session = Depends(db_dep)):
    flags = session.query(IntegrityFlag).all()
    n_q = session.query(Question).count()
    n_span = session.query(SourceSpan).count()
    return {
        "questions": n_q,
        "spans": n_span,
        "flags": [{"kind": f.kind, "item": f.item, "detail": f.detail} for f in flags],
    }


@app.get("/api/misconceptions")
def misconceptions(session: Session = Depends(db_dep)):
    rows = session.query(Misconception).all()
    return [
        {"slug": m.slug, "confused": m.confused, "missing_distinction": m.missing_distinction, "simple_correction": m.simple_correction, "source": m.source}
        for m in rows
    ]


@app.post("/api/notes")
def notes_post(body: NoteIn, session: Session = Depends(db_dep)):
    user = learner(session)
    session.add(Note(user_id=user.id, target_type=body.target_type, target_id=body.target_id, body=body.body))
    session.commit()
    return {"ok": True}


@app.get("/api/notes")
def notes_get(session: Session = Depends(db_dep)):
    user = learner(session)
    rows = session.query(Note).filter_by(user_id=user.id).all()
    return [{"id": n.id, "target_type": n.target_type, "target_id": n.target_id, "body": n.body} for n in rows]


@app.post("/api/bookmarks")
def bookmarks_post(body: NoteIn, session: Session = Depends(db_dep)):
    user = learner(session)
    session.add(Bookmark(user_id=user.id, target_type=body.target_type, target_id=body.target_id, title=body.body[:180]))
    session.commit()
    return {"ok": True}


@app.get("/api/bookmarks")
def bookmarks_get(session: Session = Depends(db_dep)):
    user = learner(session)
    rows = session.query(Bookmark).filter_by(user_id=user.id).all()
    return [{"id": b.id, "target_type": b.target_type, "target_id": b.target_id, "title": b.title} for b in rows]


@app.get("/api/assessment")
def assessment(session: Session = Depends(db_dep)):
    steps = [
        {"id": "workload", "title": "Understand the workload", "text": "You have a frozen LiDAR cube/sphere classifier. RGB cameras are cheaper. Omniverse gave paired RGB–LiDAR."},
        {"id": "hypothesis", "title": "Form a hypothesis", "text": "Contrastive Image-LiDAR Pre-training can align spaces so a projector reuses the LiDAR head."},
        {"id": "architecture", "title": "Choose architecture", "options": ["rgb_finetune_lidar_cnn", "cilp_plus_projector_frozen_head", "early_fusion_net8", "vss_summarize_pngs"]},
        {"id": "ratio", "title": "Select training recipe", "options": ["unfreeze_all", "freeze_lidar_and_cilp_train_projector", "train_only_lidar_on_rgb"]},
        {"id": "simulate", "title": "Run CILP twin", "twin": "cilp-assessment"},
        {"id": "inspect", "title": "Inspect simulated gates", "text": "Loss < 3.5 and accuracy path 0.70 → 0.95 are EXPECTED_RESULT from 05, twin is SIMULATED."},
        {"id": "import", "title": "Import real results if you have them", "href": "/experiments"},
        {"id": "normalize", "title": "Normalize metrics", "text": "Do not compare RGB accuracy on different splits without saying so."},
        {"id": "recommend", "title": "Recommend", "text": "Defend CILP + frozen lidar_cnn + projector."},
        {"id": "defend", "title": "Defend", "text": "Why unfreezing the CNN would collapse the point of the assessment."},
    ]
    return {"title": "CILP assessment arena", "source": {"source_type": "notebook", "file": "05_Assessment.ipynb", "cell_index": 2}, "steps": steps, "pass_rule": "9/10 points in the original DLI grader; here we grade reasoning + twin recipe."}


class AssessIn(BaseModel):
    architecture: str
    recipe: str
    defense: str


@app.post("/api/assessment/grade")
def assessment_grade(body: AssessIn, session: Session = Depends(db_dep)):
    user = learner(session)
    arch_ok = body.architecture == "cilp_plus_projector_frozen_head"
    recipe_ok = body.recipe == "freeze_lidar_and_cilp_train_projector"
    defense_ok = any(w in body.defense.lower() for w in ("freeze", "projector", "cilp", "unfreeze"))
    score = int(arch_ok) + int(recipe_ok) + int(defense_ok)
    st = session.query(MasteryState).filter_by(user_id=user.id, concept_slug="cilp").one_or_none()
    if st:
        apply_event(st, "design", score >= 2, score / 3)
        session.commit()
    return {
        "score": score,
        "of": 3,
        "architecture_ok": arch_ok,
        "recipe_ok": recipe_ok,
        "defense_ok": defense_ok,
        "feedback": "Grade is on reasoning, not only the dropdown. Twin metrics remain SIMULATED_RESULT.",
        "evidence_type": "TUTOR_INTERPRETATION",
    }


@app.get("/api/cost")
def cost(session: Session = Depends(db_dep)):
    traces = session.query(ProviderTrace).all()
    return {
        "calls": len(traces),
        "by_provider": _group(traces),
        "budget_usd": settings.monthly_budget_usd,
        "spent_usd": sum(t.cost_usd for t in traces),
    }


def _group(traces):
    out: dict[str, dict] = {}
    for t in traces:
        row = out.setdefault(t.provider, {"calls": 0, "input_tokens": 0, "output_tokens": 0})
        row["calls"] += 1
        row["input_tokens"] += t.input_tokens
        row["output_tokens"] += t.output_tokens
    return out


class PredictionIn(BaseModel):
    prompt: str = "pre-run prediction"
    prediction: str
    actual: dict[str, Any] = Field(default_factory=dict)


class VoiceTtsIn(BaseModel):
    text: str
    provider: str = "auto"
    language: str = "en"
    clip: bool = False


class TutorSessionIn(BaseModel):
    mode: str = "course"
    depth: str = "engineer"
    provider: str = "auto"


class TutorMessageIn(BaseModel):
    message: str
    mode: str | None = None
    depth: str | None = None
    provider: str | None = None


@app.get("/api/twins/{slug}/suggestions")
def twin_suggestions(slug: str):
    if slug not in SCENARIOS:
        raise HTTPException(404, "Unknown twin")
    return SUGGESTED_SCENARIOS.get(slug, [])


@app.post("/api/twins/{slug}/predictions")
def twin_predict(slug: str, body: PredictionIn, session: Session = Depends(db_dep)):
    if slug not in SCENARIOS:
        raise HTTPException(404, "Unknown twin")
    user = learner(session)
    row = LearnerPrediction(
        user_id=user.id,
        twin_id=slug,
        prompt=body.prompt,
        prediction=body.prediction,
        actual=body.actual,
        evidence_type="SIMULATED_RESULT",
    )
    session.add(row)
    session.commit()
    return {"id": row.id, "twin": slug, "prediction": body.prediction, "evidence_type": "SIMULATED_RESULT"}


@app.get("/api/twins/{slug}/predictions")
def twin_predictions(slug: str, session: Session = Depends(db_dep)):
    user = learner(session)
    rows = session.query(LearnerPrediction).filter_by(user_id=user.id, twin_id=slug).all()
    return [
        {"id": r.id, "prompt": r.prompt, "prediction": r.prediction, "actual": r.actual, "evidence_type": r.evidence_type}
        for r in rows
    ]


@app.get("/api/risks")
def risks():
    return RISKS


@app.get("/api/setup")
def setup_checklist(session: Session = Depends(db_dep)):
    n_nb = session.query(Notebook).count()
    n_q = session.query(Question).count()
    n_c = session.query(Concept).count()
    items = [
        {"id": "demo", "label": "Offline demo tutor (zero-key)", "ok": True, "required": True},
        {"id": "materials", "label": "course-materials ingested", "ok": n_nb >= 8, "required": True, "count": n_nb},
        {"id": "concepts", "label": "Concept graph seeded", "ok": n_c >= 80, "count": n_c},
        {"id": "questions", "label": "Question bank", "ok": n_q >= 400, "count": n_q},
        {"id": "openai", "label": "OpenAI tutor", "ok": bool(settings.openai_api_key), "required": False},
        {"id": "nim", "label": "NVIDIA NIM tutor", "ok": bool(settings.nvidia_api_key), "required": False},
        {"id": "huggingface", "label": "Hugging Face tutor", "ok": bool(settings.hf_token), "required": False},
        {"id": "elevenlabs", "label": "ElevenLabs TTS", "ok": bool(settings.elevenlabs_api_key), "required": False},
        {"id": "sarvam", "label": "Sarvam Indic TTS", "ok": bool(settings.sarvam_api_key), "required": False},
        {"id": "perplexity", "label": "Perplexity research", "ok": bool(settings.perplexity_api_key), "required": False},
    ]
    return {
        "items": items,
        "go_live": all(i["ok"] for i in items if i.get("required")),
        "note": "Keys only enhance. The core academy works with Demo and browser voice.",
        "disclaimer": "Not affiliated with or endorsed by NVIDIA.",
    }


@app.get("/api/voice/status")
def api_voice_status():
    return voice_status()


@app.post("/api/voice/tts")
def api_voice_tts(body: VoiceTtsIn):
    return tts_payload(body.text, provider=body.provider, language=body.language, clip=body.clip)


@app.post("/api/voice/stt")
async def api_voice_stt(text: str = Form(""), file: UploadFile | None = File(None)):
    if text.strip():
        return {"text": text.strip(), "provider": "passthrough", "evidence_type": "TUTOR_INTERPRETATION"}
    if file:
        return {
            "text": "",
            "provider": "browser_fallback",
            "filename": file.filename,
            "note": "Server STT needs a provider key. Use the browser SpeechRecognition fallback.",
        }
    return {"text": "", "provider": "browser_fallback"}


@app.get("/api/learning/reviews/due")
def reviews_due(session: Session = Depends(db_dep)):
    user = learner(session)
    now = datetime.now(timezone.utc)
    rows = session.query(ReviewItem).filter(ReviewItem.user_id == user.id).all()
    due = []
    for item in rows:
        due_at = item.due
        if due_at is not None and due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        if due_at is None or due_at <= now:
            due.append(
                {
                    "id": item.id,
                    "concept": item.concept_slug,
                    "due": item.due.isoformat() if item.due else None,
                    "reason": item.reason,
                    "question_id": item.question_id,
                }
            )
    return {"due": due, "count": len(due)}


@app.get("/api/learning/mastery")
def learning_mastery(session: Session = Depends(db_dep)):
    return progress(session)


@app.get("/api/learning/diagnostics")
def learning_diagnostics(session: Session = Depends(db_dep)):
    return diagnostic(session)


@app.post("/api/tutor/sessions")
def tutor_session_create(body: TutorSessionIn, session: Session = Depends(db_dep)):
    user = learner(session)
    provider = body.provider if body.provider and body.provider != "auto" else "demo"
    ts = TutorSession(user_id=user.id, mode=body.mode, depth=body.depth, provider=provider)
    session.add(ts)
    session.commit()
    return {"id": ts.id, "mode": ts.mode, "depth": ts.depth, "provider": ts.provider}


@app.post("/api/tutor/sessions/{sid}/messages")
def tutor_session_message(sid: int, body: TutorMessageIn, session: Session = Depends(db_dep)):
    user = learner(session)
    ts = session.get(TutorSession, sid)
    if not ts:
        raise HTTPException(404, "Unknown tutor session")
    ps = session.query(ProviderSetting).filter_by(user_id=user.id).one_or_none()
    provider = body.provider or ts.provider or (ps.tutor_provider if ps else "demo")
    if provider == "auto":
        provider = ps.tutor_provider if ps else "demo"
    mode = body.mode or ts.mode
    depth = body.depth or ts.depth
    result = tutor_turn(
        session,
        user.id,
        body.message,
        mode=mode,
        depth=depth,
        provider_name=provider,
        tutor_session_id=sid,
    )
    session.add(
        ProviderTrace(
            provider=result["telemetry"]["provider"],
            model=result["telemetry"].get("model") or "",
            feature="tutor",
            input_tokens=result["telemetry"].get("input_tokens") or 0,
            output_tokens=result["telemetry"].get("output_tokens") or 0,
            latency_ms=result["telemetry"].get("latency_ms") or 0,
            ttft_ms=result["telemetry"].get("ttft_ms"),
            tpot_ms=result["telemetry"].get("tpot_ms"),
        )
    )
    session.commit()

    def events():
        text = result.get("text") or ""
        for i in range(0, max(len(text), 1), 48):
            chunk = text[i : i + 48]
            yield f"data: {json.dumps({'delta': chunk, 'telemetry': result.get('telemetry')})}\n\n"
        payload = {k: v for k, v in result.items() if k != "text"}
        payload["done"] = True
        payload["text"] = text
        yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")

