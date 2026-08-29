from __future__ import annotations

from .db import (
    Concept,
    ConceptEdge,
    DigitalTwin,
    IntegrityFlag,
    LearningObjective,
    Lesson,
    MasteryState,
    Misconception,
    ProviderSetting,
    Question,
    TwinScenario,
    User,
    get_session,
)
from .ingest import ingest_all
from .knowledge import CONCEPTS, EDGES, MISCONCEPTIONS, OBJECTIVES, TWINS_CATALOG, lesson_for
from .questions import build_questions


def seed() -> dict:
    session = get_session()
    try:
        user = session.query(User).filter_by(handle="learner").one_or_none()
        if not user:
            user = User(handle="learner", display_name="Learner")
            session.add(user)
            session.flush()
            session.add(ProviderSetting(user_id=user.id, tutor_provider="demo"))

        ingest_stats = ingest_all(session)
        upsert_stats = _upsert_knowledge(session, user)
        flags = _integrity_pass(session)
        session.commit()

        return {
            "user_id": user.id,
            "ingest": ingest_stats,
            "concepts": session.query(Concept).count(),
            "questions": session.query(Question).count(),
            "twins": session.query(DigitalTwin).count(),
            "upsert": upsert_stats,
            "integrity_flags_new": flags,
        }
    finally:
        session.close()


def _upsert_knowledge(session, user: User) -> dict:
    added = {"concepts": 0, "twins": 0, "questions": 0, "lessons": 0, "misconceptions": 0}

    existing_concepts = {row.slug: row for row in session.query(Concept).all()}
    for c in CONCEPTS:
        payload = {
            "name": c["name"],
            "cluster": c.get("cluster") or "fundamentals",
            "school": c["school"],
            "engineer": c["engineer"],
            "research": c["research"],
            "analogy": c.get("analogy") or "",
            "twin_id": c.get("twin_id") or "",
            "source": c.get("source") or {},
            "common_misconceptions": c.get("misconceptions") or [],
        }
        row = existing_concepts.get(c["slug"])
        if row:
            for key, value in payload.items():
                setattr(row, key, value)
        else:
            session.add(Concept(slug=c["slug"], **payload))
            added["concepts"] += 1

    if not session.query(ConceptEdge).first():
        for src, dst, rel, note in EDGES:
            session.add(ConceptEdge(src=src, dst=dst, relation=rel, note=note))

    existing_misc = {row.slug: row for row in session.query(Misconception).all()}
    for m in MISCONCEPTIONS:
        row = existing_misc.get(m["slug"])
        if row:
            row.confused = m["confused"]
            row.missing_distinction = m["missing_distinction"]
            row.simple_correction = m["simple_correction"]
            row.source = m.get("source") or {}
        else:
            session.add(Misconception(**m))
            added["misconceptions"] += 1

    existing_obj = {row.slug for row in session.query(LearningObjective).all()}
    for slug, text, concept, nb, level in OBJECTIVES:
        if slug not in existing_obj:
            session.add(
                LearningObjective(slug=slug, text=text, concept_slug=concept, notebook=nb, level=level)
            )

    existing_lessons = {row.slug: row for row in session.query(Lesson).all()}
    for c in CONCEPTS:
        lesson = lesson_for(c)
        row = existing_lessons.get(lesson["slug"])
        if row:
            row.title = lesson["title"]
            row.steps = lesson["steps"]
            row.twin_id = lesson["twin_id"]
        else:
            session.add(Lesson(**lesson))
            added["lessons"] += 1

    existing_twins = {row.slug: row for row in session.query(DigitalTwin).all()}
    existing_scenarios = {(row.twin_slug, row.name) for row in session.query(TwinScenario).all()}
    for twin in TWINS_CATALOG:
        row = existing_twins.get(twin["slug"])
        if row:
            row.title = twin["title"]
            row.summary = twin["summary"]
            row.controls = twin["controls"]
        else:
            session.add(
                DigitalTwin(
                    slug=twin["slug"],
                    title=twin["title"],
                    summary=twin["summary"],
                    controls=twin["controls"],
                )
            )
            added["twins"] += 1
        key = (twin["slug"], "default")
        if key not in existing_scenarios:
            session.add(
                TwinScenario(
                    twin_slug=twin["slug"],
                    name="default",
                    controls={ctl["key"]: ctl.get("default") for ctl in twin["controls"]},
                    teach=twin["summary"],
                )
            )

    existing_q = {row.slug for row in session.query(Question).all()}
    for q in build_questions():
        if q["slug"] not in existing_q:
            session.add(Question(**q))
            added["questions"] += 1
            existing_q.add(q["slug"])

    existing_m = {row.concept_slug for row in session.query(MasteryState).filter_by(user_id=user.id).all()}
    for c in CONCEPTS:
        if c["slug"] not in existing_m:
            session.add(MasteryState(user_id=user.id, concept_slug=c["slug"]))

    session.flush()
    return added


def _integrity_pass(session) -> int:
    flags = 0
    if session.query(IntegrityFlag).first():
        return 0
    n_q = session.query(Question).count()
    for q in session.query(Question).all():
        src = q.source or {}
        if not src.get("file"):
            session.add(IntegrityFlag(kind="unsupported", item=q.slug, detail="Missing source file"))
            flags += 1
        if not q.explanation:
            session.add(IntegrityFlag(kind="unsupported", item=q.slug, detail="Missing explanation"))
            flags += 1
    session.add(
        IntegrityFlag(
            kind="sourced",
            item="questions",
            detail=f"{n_q} questions generated with notebook locators",
        )
    )
    return flags
