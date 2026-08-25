from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from .db import MasteryState, ReviewItem, utcnow

WEIGHTS = {
    "viewed": 0.08,
    "recognition": 0.12,
    "recall": 0.28,
    "explain": 0.45,
    "predict": 0.62,
    "diagnose": 0.68,
    "apply": 0.8,
    "design": 0.92,
    "teachback": 0.88,
}


def explain_mastery(state: MasteryState) -> dict:
    evidence = {
        "viewed": min(1.0, state.viewed / 5) * WEIGHTS["viewed"],
        "recognition_recall": (state.correct_attempts / max(state.attempts, 1)) * WEIGHTS["recall"] * min(1.0, state.attempts / 4),
        "explain": state.explain_quality * WEIGHTS["explain"],
        "predict": state.predict_quality * WEIGHTS["predict"],
        "diagnose": state.diagnose_quality * WEIGHTS["diagnose"],
        "teachback": state.teachback_quality * WEIGHTS["teachback"],
    }
    raw = sum(evidence.values())
    score = 1 - math.exp(-raw * 1.4)
    return {
        "score": round(score, 4),
        "evidence": {k: round(v, 4) for k, v in evidence.items()},
        "note": "Viewing content is low weight. Predict, diagnose, apply, and teach-back move mastery.",
    }


def apply_event(state: MasteryState, kind: str, success: bool, quality: float = 0.0, misconception: str | None = None) -> MasteryState:
    if kind != "viewed":
        state.attempts += 1
        if success:
            state.correct_attempts += 1
    if kind == "viewed":
        state.viewed += 1
    if kind in {"explain", "teachback", "predict", "diagnose"}:
        q = max(quality, 1.0 if success else 0.2)
        if kind == "explain":
            state.explain_quality = _ema(state.explain_quality, q)
        elif kind == "teachback":
            state.teachback_quality = _ema(state.teachback_quality, q)
        elif kind == "predict":
            state.predict_quality = _ema(state.predict_quality, q)
        elif kind == "diagnose":
            state.diagnose_quality = _ema(state.diagnose_quality, q)
    if misconception:
        tags = list(state.misconception_tags or [])
        if misconception not in tags:
            tags.append(misconception)
        if success and misconception in tags:
            tags = [t for t in tags if t != misconception]
        state.misconception_tags = tags
    rating = 4 if success and quality >= 0.8 else 3 if success else 1 if quality < 0.3 else 2
    fsrs_update(state, rating)
    breakdown = explain_mastery(state)
    state.score = breakdown["score"]
    state.confidence = min(0.95, 0.2 + 0.08 * state.attempts + 0.3 * state.score)
    return state


def _ema(prev: float, value: float, alpha: float = 0.35) -> float:
    return (1 - alpha) * prev + alpha * value


def fsrs_update(state: MasteryState, rating: int) -> None:
    """Explainable FSRS-inspired update (stability/difficulty + next_review)."""
    now = utcnow()
    last = state.last_reviewed or now
    elapsed = max((now - last).total_seconds() / 86400.0, 0.01)
    d = state.difficulty
    s = max(state.stability, 0.1)
    # Difficulty: harder after lapses
    d = d + (rating - 3) * (-0.35)
    d = min(10.0, max(1.0, d))
    if rating == 1:
        s = max(0.3, s * 0.4)
    else:
        s = s * (1.3 + (4 - d) * 0.08) * (elapsed**0.1)
        s = min(s, 60.0)
    interval = s * (0.9 + 0.15 * rating)
    state.difficulty = d
    state.stability = s
    state.last_reviewed = now
    state.next_review = now + timedelta(days=max(0.04, interval))


def schedule_review(session, user_id: int, concept_slug: str, question_id: int | None, reason: str) -> None:
    session.add(
        ReviewItem(
            user_id=user_id,
            question_id=question_id,
            concept_slug=concept_slug,
            due=utcnow() + timedelta(hours=4 if reason == "wrong" else 24),
            reason=reason,
        )
    )
