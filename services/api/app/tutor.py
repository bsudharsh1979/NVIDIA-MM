from __future__ import annotations

import re
from typing import Any

from .db import MasteryState, TutorMessage, TutorSession, get_session
from .ingest import hybrid_search
from .knowledge import CONCEPTS, MISCONCEPTIONS
from .mastery import apply_event
from .providers import PerplexityResearchProvider, get_tutor_provider

INTENTS = [
    ("simpler", r"\b(simpler|eli5|school|analogy)\b"),
    ("deeper", r"\b(deeper|research|math|engineer mode)\b"),
    ("source", r"\b(show source|citation|view source|notebook cell)\b"),
    ("quiz", r"\b(quiz|test me|challenge)\b"),
    ("hint", r"\b(hint|don't reveal|do not reveal)\b"),
    ("twin", r"\b(digital twin|run scenario|what happens if)\b"),
    ("teachback", r"\b(let me (explain|teach)|teach-?back)\b"),
    ("telemetry", r"\b(telemetry|how this answer was served|ttft|tpot)\b"),
    ("next", r"\b(what should i learn next|next)\b"),
    ("compare", r"\bcompare\b"),
]


def detect_intent(text: str) -> str:
    t = text.lower()
    for name, pat in INTENTS:
        if re.search(pat, t):
            return name
    return "explain"


def detect_concepts(text: str) -> list[str]:
    t = text.lower()
    hits = []
    for c in CONCEPTS:
        if c["slug"].replace("-", " ") in t or c["name"].lower() in t:
            hits.append(c["slug"])
        else:
            for word in c["name"].lower().split():
                if len(word) > 4 and word in t:
                    hits.append(c["slug"])
                    break
    # unique preserve
    seen = []
    for h in hits:
        if h not in seen:
            seen.append(h)
    return seen[:6]


def tutor_turn(
    session,
    user_id: int,
    message: str,
    *,
    mode: str = "course",
    depth: str = "engineer",
    provider_name: str = "demo",
    tutor_session_id: int | None = None,
) -> dict:
    intent = detect_intent(message)
    concepts = detect_concepts(message)
    retrieved = hybrid_search(session, message, k=6)
    if tutor_session_id is None:
        ts = TutorSession(user_id=user_id, mode=mode, depth=depth, provider=provider_name)
        session.add(ts)
        session.flush()
        tutor_session_id = ts.id
    session.add(TutorMessage(session_id=tutor_session_id, role="user", content=message, evidence_type="COURSE_SOURCE"))

    if intent == "teachback":
        result = grade_teachback(message, concepts)
        session.add(
            TutorMessage(
                session_id=tutor_session_id,
                role="assistant",
                content=result["feedback"],
                citations=retrieved,
                evidence_type="TUTOR_INTERPRETATION",
            )
        )
        _bump(session, user_id, concepts, "teachback", result["quality"] >= 0.6, result["quality"])
        session.commit()
        return {**result, "session_id": tutor_session_id, "intent": intent, "citations": retrieved}

    research_block = None
    if mode == "research" and PerplexityResearchProvider().available():
        research_block = PerplexityResearchProvider().search(message)

    depth_prefix = {
        "school": "Explain like a bright Grade-12 student, one analogy, minimal equations.",
        "engineer": "Use real terminology, tensors, APIs, operational consequences.",
        "research": "Include caveats, hardware/memory implications, and experimental limits. Do not invent NVIDIA results.",
    }[depth if depth in {"school", "engineer", "research"} else "engineer"]

    system = (
        "You are the Modality Twin Academy tutor for NVIDIA DLI Building Multimodal AI Applications. "
        "Never present SIMULATED_RESULT as ACTUAL_RUN. Never execute notebook shell. "
        f"{depth_prefix} "
        "If Course Mode and the retrieved spans do not support the claim, say: "
        "'This is not established by the supplied course material.'"
    )
    if mode == "course":
        system += " Do not use the public web. Only course spans and learner notes."

    ctx_text = "\n\n".join(
        f"[{c['locator']}] {c['text']}" for c in retrieved
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Retrieved evidence:\n{ctx_text}\n\nLearner ({intent}): {message}"},
    ]
    if research_block and research_block.get("text"):
        messages.append(
            {
                "role": "system",
                "content": "EXTERNAL_RESEARCH (do not overwrite course definitions):\n" + research_block["text"][:3000],
            }
        )

    provider = get_tutor_provider(provider_name if provider_name != "demo" or retrieved else "demo")
    # Course mode without keys still uses demo even if user selected openai
    if not provider.available():
        fallback = "demo"
        provider = get_tutor_provider("demo")
        switched = f"Requested {provider_name} is unavailable; using demo (disclosed, not silent)."
    else:
        fallback = None
        switched = None

    result = provider.complete(messages, context=retrieved, mode=mode, temperature=0.2)
    if result.error:
        provider = get_tutor_provider("demo")
        result = provider.complete(messages, context=retrieved, mode=mode)
        switched = f"{provider_name} error: {result.error}. Fell back to demo."

    text = result.text
    if intent == "simpler":
        text = _school_rewrite(text, concepts)
    if research_block and research_block.get("text"):
        text += "\n\n🟣 EXTERNAL_RESEARCH (does not override COURSE_SOURCE).\n"
    if switched:
        text = f"_{switched}_\n\n" + text

    telemetry = {
        "provider": result.provider,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "latency_ms": round(result.latency_ms, 2),
        "ttft_ms": result.ttft_ms,
        "tpot_ms": result.tpot_ms,
        "tokens_per_sec": result.tokens_per_sec,
        "evidence_type": result.evidence_type,
    }
    session.add(
        TutorMessage(
            session_id=tutor_session_id,
            role="assistant",
            content=text,
            citations=retrieved,
            evidence_type=result.evidence_type,
            telemetry=telemetry,
        )
    )
    _bump(session, user_id, concepts, "viewed", True, 0.3)
    session.commit()
    return {
        "session_id": tutor_session_id,
        "intent": intent,
        "concepts": concepts,
        "text": text,
        "citations": retrieved,
        "telemetry": telemetry,
        "provider_disclosure": switched,
        "research": research_block,
        "depth": depth,
        "mode": mode,
    }


def _school_rewrite(text: str, concepts: list[str]) -> str:
    if not concepts:
        return "Analogy: think of extra senses. " + text[:800]
    c = next((x for x in CONCEPTS if x["slug"] == concepts[0]), None)
    if not c:
        return text
    return f"**School mode — {c['name']}**\n{c['school']}\n\n(Engineer detail still available on request.)\n"


def grade_teachback(text: str, concepts: list[str]) -> dict:
    required = []
    for slug in concepts or ["late-fusion"]:
        c = next((x for x in CONCEPTS if x["slug"] == slug), None)
        if c:
            required.append(c)
    if not required:
        required = CONCEPTS[:1]
    blob = text.lower()
    correctly, partial, missing, confused = [], [], [], []
    keywords = {
        "late-fusion": ["late", "head", "ensemble", "end"],
        "early-fusion": ["channel", "concat", "beginning", "stack"],
        "cilp": ["contrastive", "lidar", "image", "freeze"],
        "graph-rag": ["neo4j", "cypher", "extraction", "relation"],
        "vss-chunk-duration": ["chunk", "frames", "duration"],
        "lidar-xyza": ["azimuth", "zenith", "sin", "mask"],
    }
    for c in required:
        keys = keywords.get(c["slug"], c["name"].lower().split())
        hits = sum(1 for k in keys if k in blob)
        if hits >= max(2, len(keys) // 2):
            correctly.append(c["name"])
        elif hits == 1:
            partial.append(c["name"])
        else:
            missing.append(c["name"])
    for m in MISCONCEPTIONS:
        if m["confused"].split()[0].lower() in blob and m["simple_correction"].split()[0].lower() not in blob:
            confused.append(m["slug"])
    quality = (len(correctly) + 0.5 * len(partial)) / max(len(required), 1)
    feedback = (
        f"### Correctly explained\n- " + ("\n- ".join(correctly) or "None yet")
        + f"\n\n### Partially explained\n- " + ("\n- ".join(partial) or "None")
        + f"\n\n### Missing\n- " + ("\n- ".join(missing) or "None")
        + f"\n\n### Confused concepts\n- " + ("\n- ".join(confused) or "None flagged")
        + "\n\n### Suggested improved explanation\n"
        + required[0]["engineer"]
    )
    return {"feedback": feedback, "quality": quality, "correctly": correctly, "missing": missing, "confused": confused}


def _bump(session, user_id, concepts, kind, success, quality):
    for slug in concepts or []:
        state = session.query(MasteryState).filter_by(user_id=user_id, concept_slug=slug).one_or_none()
        if not state:
            state = MasteryState(user_id=user_id, concept_slug=slug)
            session.add(state)
            session.flush()
        apply_event(state, kind, success, quality)


def why_wrong(user_answer: str, question: dict) -> dict:
    m = next((x for x in MISCONCEPTIONS if x["slug"] == question.get("misconception_slug")), None)
    return {
        "your_answer": user_answer,
        "what_this_suggests": m["confused"] if m else "A nearby but incorrect operational picture of the concept.",
        "missing_distinction": m["missing_distinction"] if m else question.get("explanation"),
        "source_evidence": question.get("source"),
        "simple_correction": m["simple_correction"] if m else question.get("explanation"),
        "try_again": True,
        "evidence_type": "COURSE_SOURCE",
    }
