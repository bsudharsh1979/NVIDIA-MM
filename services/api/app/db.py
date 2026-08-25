from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

from .config import settings


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    handle: Mapped[str] = mapped_column(String(80), unique=True)
    display_name: Mapped[str] = mapped_column(String(120), default="Learner")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_resume_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")


class SourceArtifact(Base):
    __tablename__ = "source_artifacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    source_type: Mapped[str] = mapped_column(String(40))
    filename: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255), default="")
    checksum: Mapped[str] = mapped_column(String(64), default="")
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class SourceSpan(Base):
    __tablename__ = "source_spans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("source_artifacts.id"))
    span_type: Mapped[str] = mapped_column(String(40))
    locator: Mapped[dict] = mapped_column(JSON)
    title: Mapped[str] = mapped_column(String(255), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    code: Mapped[str] = mapped_column(Text, default="")
    stored_output: Mapped[str] = mapped_column(Text, default="")
    heading: Mapped[str] = mapped_column(String(255), default="")
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    __table_args__ = (Index("ix_span_artifact", "artifact_id"),)


class Notebook(Base):
    __tablename__ = "notebooks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("source_artifacts.id"))
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    purpose: Mapped[str] = mapped_column(Text, default="")
    why_it_matters: Mapped[str] = mapped_column(Text, default="")
    expected_outcome: Mapped[str] = mapped_column(Text, default="")


class NotebookCell(Base):
    __tablename__ = "notebook_cells"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notebook_id: Mapped[int] = mapped_column(ForeignKey("notebooks.id"))
    span_id: Mapped[Optional[int]] = mapped_column(ForeignKey("source_spans.id"), nullable=True)
    cell_index: Mapped[int] = mapped_column(Integer)
    cell_type: Mapped[str] = mapped_column(String(20))
    execution_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    markdown: Mapped[str] = mapped_column(Text, default="")
    code: Mapped[str] = mapped_column(Text, default="")
    stored_output: Mapped[str] = mapped_column(Text, default="")
    heading: Mapped[str] = mapped_column(String(255), default="")
    commands: Mapped[list] = mapped_column(JSON, default=list)
    dangerous: Mapped[bool] = mapped_column(Boolean, default=False)
    extras: Mapped[dict] = mapped_column(JSON, default=dict)


class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    cluster: Mapped[str] = mapped_column(String(80))
    school: Mapped[str] = mapped_column(Text)
    engineer: Mapped[str] = mapped_column(Text)
    research: Mapped[str] = mapped_column(Text)
    twin_id: Mapped[str] = mapped_column(String(80), default="")
    source: Mapped[dict] = mapped_column(JSON, default=dict)
    common_misconceptions: Mapped[list] = mapped_column(JSON, default=list)


class ConceptEdge(Base):
    __tablename__ = "concept_edges"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    src: Mapped[str] = mapped_column(String(120))
    dst: Mapped[str] = mapped_column(String(120))
    relation: Mapped[str] = mapped_column(String(40))
    note: Mapped[str] = mapped_column(Text, default="")


class LearningObjective(Base):
    __tablename__ = "learning_objectives"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    text: Mapped[str] = mapped_column(Text)
    concept_slug: Mapped[str] = mapped_column(String(120))
    notebook: Mapped[str] = mapped_column(String(160), default="")
    level: Mapped[int] = mapped_column(Integer, default=1)


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    concept_slug: Mapped[str] = mapped_column(String(120))
    steps: Mapped[list] = mapped_column(JSON, default=list)
    twin_id: Mapped[str] = mapped_column(String(80), default="")


class Misconception(Base):
    __tablename__ = "misconceptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    confused: Mapped[str] = mapped_column(String(200))
    missing_distinction: Mapped[str] = mapped_column(Text)
    simple_correction: Mapped[str] = mapped_column(Text)
    source: Mapped[dict] = mapped_column(JSON, default=dict)


class MasteryState(Base):
    __tablename__ = "mastery_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    concept_slug: Mapped[str] = mapped_column(String(120))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.2)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    viewed: Mapped[int] = mapped_column(Integer, default=0)
    explain_quality: Mapped[float] = mapped_column(Float, default=0.0)
    predict_quality: Mapped[float] = mapped_column(Float, default=0.0)
    diagnose_quality: Mapped[float] = mapped_column(Float, default=0.0)
    teachback_quality: Mapped[float] = mapped_column(Float, default=0.0)
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_review: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stability: Mapped[float] = mapped_column(Float, default=1.0)
    difficulty: Mapped[float] = mapped_column(Float, default=5.0)
    misconception_tags: Mapped[list] = mapped_column(JSON, default=list)
    __table_args__ = (UniqueConstraint("user_id", "concept_slug"),)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True)
    qtype: Mapped[str] = mapped_column(String(40))
    bloom: Mapped[str] = mapped_column(String(40))
    difficulty: Mapped[int] = mapped_column(Integer, default=2)
    concept_slug: Mapped[str] = mapped_column(String(120))
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    source: Mapped[dict] = mapped_column(JSON, default=dict)
    misconception_slug: Mapped[str] = mapped_column(String(160), default="")
    validated: Mapped[bool] = mapped_column(Boolean, default=True)


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    response: Mapped[str] = mapped_column(Text)
    correct: Mapped[bool] = mapped_column(Boolean, default=False)
    hints: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    feedback: Mapped[dict] = mapped_column(JSON, default=dict)


class ReviewItem(Base):
    __tablename__ = "review_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey("questions.id"), nullable=True)
    concept_slug: Mapped[str] = mapped_column(String(120))
    due: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    reason: Mapped[str] = mapped_column(String(80), default="weak")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class TutorSession(Base):
    __tablename__ = "tutor_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    mode: Mapped[str] = mapped_column(String(20), default="course")
    depth: Mapped[str] = mapped_column(String(20), default="engineer")
    provider: Mapped[str] = mapped_column(String(40), default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TutorMessage(Base):
    __tablename__ = "tutor_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("tutor_sessions.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    evidence_type: Mapped[str] = mapped_column(String(40), default="TUTOR_INTERPRETATION")
    telemetry: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LearnerPrediction(Base):
    __tablename__ = "learner_predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    twin_id: Mapped[str] = mapped_column(String(80))
    prompt: Mapped[str] = mapped_column(Text)
    prediction: Mapped[str] = mapped_column(Text)
    actual: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_type: Mapped[str] = mapped_column(String(40), default="SIMULATED_RESULT")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DigitalTwin(Base):
    __tablename__ = "digital_twins"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(Text)
    controls: Mapped[list] = mapped_column(JSON, default=list)


class TwinScenario(Base):
    __tablename__ = "twin_scenarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    twin_slug: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    controls: Mapped[dict] = mapped_column(JSON, default=dict)
    teach: Mapped[str] = mapped_column(Text, default="")


class TwinRun(Base):
    __tablename__ = "twin_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    twin_slug: Mapped[str] = mapped_column(String(80))
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(40))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    evidence_type: Mapped[str] = mapped_column(String(40), default="ACTUAL_RUN")
    raw_ref: Mapped[str] = mapped_column(String(255), default="")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)


class EvidenceArtifact(Base):
    __tablename__ = "evidence_artifacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_type: Mapped[str] = mapped_column(String(40))
    label: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[dict] = mapped_column(JSON, default=dict)


class ProviderTrace(Base):
    __tablename__ = "provider_traces"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120), default="")
    feature: Mapped[str] = mapped_column(String(80), default="tutor")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    ttft_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tpot_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ProviderSetting(Base):
    __tablename__ = "provider_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    tutor_provider: Mapped[str] = mapped_column(String(40), default="demo")
    voice_provider: Mapped[str] = mapped_column(String(40), default="off")
    research_provider: Mapped[str] = mapped_column(String(40), default="off")
    depth: Mapped[str] = mapped_column(String(20), default="engineer")
    course_mode: Mapped[str] = mapped_column(String(20), default="course")


class IntegrityFlag(Base):
    __tablename__ = "integrity_flags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(40))
    item: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str] = mapped_column(Text)


_engine = None
SessionLocal: sessionmaker | None = None


def get_engine():
    global _engine, SessionLocal
    if _engine is None:
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
        SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def init_db() -> None:
    engine = get_engine()
    if settings.database_url.startswith("sqlite"):
        from pathlib import Path

        path = settings.database_url.replace("sqlite:///", "")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


def get_session() -> Session:
    get_engine()
    assert SessionLocal is not None
    return SessionLocal()
