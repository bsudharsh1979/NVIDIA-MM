"""Resolve notebooks/sources/spans by uid, slug, or filename. 404s explain staleness."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .db import Notebook, SourceArtifact, SourceSpan

STALE_NOTEBOOK = (
    "Unknown notebook. Content ids are deterministic sha1(path) values, not random UUIDs. "
    "Modal SQLite is ephemeral — if you bookmarked an old id, this link is stale. "
    "Open /notebooks and use the current id, slug, or filename (for example "
    "01a_Early_and_Late_Fusion.ipynb)."
)
STALE_SOURCE = (
    "Unknown source. Ids are sha1(path). If this bookmark predates a cold start, it is stale. "
    "Open /sources and pick the file by name."
)
STALE_SPAN = (
    "Unknown span. Span ids are sha1(artifact:locator:kind:seq). "
    "A Modal cold start with a fresh SQLite file invalidates old integer ids — "
    "re-open the notebook or source and copy the current span id."
)


def resolve_notebook(session: Session, key: str) -> Notebook:
    raw = (key or "").strip()
    if not raw:
        raise HTTPException(status_code=404, detail=STALE_NOTEBOOK)
    nb = session.query(Notebook).filter_by(uid=raw).one_or_none()
    if nb:
        return nb
    slug = raw[:-6] if raw.endswith(".ipynb") else raw
    nb = session.query(Notebook).filter_by(slug=slug).one_or_none()
    if nb:
        return nb
    art = (
        session.query(SourceArtifact)
        .filter(
            (SourceArtifact.filename == raw)
            | (SourceArtifact.filename == raw + ".ipynb")
            | (SourceArtifact.uid == raw)
        )
        .first()
    )
    if art:
        nb = session.query(Notebook).filter_by(artifact_id=art.id).one_or_none()
        if nb:
            return nb
    if raw.isdigit():
        nb = session.get(Notebook, int(raw))
        if nb:
            return nb
    raise HTTPException(status_code=404, detail=STALE_NOTEBOOK)


def resolve_source(session: Session, key: str) -> SourceArtifact:
    raw = (key or "").strip()
    if not raw:
        raise HTTPException(status_code=404, detail=STALE_SOURCE)
    if raw.isdigit():
        art = session.get(SourceArtifact, int(raw))
        if art:
            return art
    art = (
        session.query(SourceArtifact)
        .filter(
            (SourceArtifact.uid == raw)
            | (SourceArtifact.filename == raw)
            | (SourceArtifact.filename == raw + ".ipynb")
        )
        .first()
    )
    if art:
        return art
    raise HTTPException(status_code=404, detail=STALE_SOURCE)


def resolve_span(session: Session, key: str) -> SourceSpan:
    raw = (key or "").strip()
    if not raw:
        raise HTTPException(status_code=404, detail=STALE_SPAN)
    if raw.isdigit():
        span = session.get(SourceSpan, int(raw))
        if span:
            return span
    span = session.query(SourceSpan).filter_by(uid=raw).one_or_none()
    if span:
        return span
    raise HTTPException(status_code=404, detail=STALE_SPAN)
