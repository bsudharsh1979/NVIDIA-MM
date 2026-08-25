from __future__ import annotations

from .db import (
    Concept,
    ConceptEdge,
    Course,
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

        if not session.query(Concept).first():
            for c in CONCEPTS:
                payload = dict(c)
                payload["common_misconceptions"] = payload.pop("misconceptions", [])
                session.add(Concept(**payload))
            for src, dst, rel, note in EDGES:
                session.add(ConceptEdge(src=src, dst=dst, relation=rel, note=note))
            for m in MISCONCEPTIONS:
                session.add(Misconception(**m))
            for slug, text, concept, nb, level in OBJECTIVES:
                session.add(
                    LearningObjective(slug=slug, text=text, concept_slug=concept, notebook=nb, level=level)
                )
            for c in CONCEPTS:
                lesson = lesson_for(c)
                session.add(Lesson(**lesson))
            for twin in TWINS_CATALOG:
                session.add(
                    DigitalTwin(
                        slug=twin["slug"],
                        title=twin["title"],
                        summary=twin["summary"],
                        controls=twin["controls"],
                    )
                )
                session.add(
                    TwinScenario(
                        twin_slug=twin["slug"],
                        name="default",
                        controls={ctl["key"]: ctl.get("default") for ctl in twin["controls"]},
                        teach=twin["summary"],
                    )
                )
            for q in build_questions():
                session.add(Question(**q))
            for c in CONCEPTS:
                session.add(MasteryState(user_id=user.id, concept_slug=c["slug"]))
            session.commit()

        n_q = session.query(Question).count()
        n_c = session.query(Concept).count()
        unsupported = session.query(Question).filter(Question.source["file"].as_string() == "").count() if False else 0
        # Integrity: every question must have source file
        flags = 0
        if not session.query(IntegrityFlag).first():
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
            session.commit()

        return {
            "user_id": user.id,
            "ingest": ingest_stats,
            "concepts": n_c,
            "questions": n_q,
            "integrity_flags_new": flags,
        }
    finally:
        session.close()
