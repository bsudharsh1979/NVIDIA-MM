from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "services" / "twin-engine"))

os.environ.setdefault("DATABASE_URL", "sqlite:///" + str(ROOT / "services" / "api" / "data" / "test.db"))
os.environ.setdefault("COURSE_MATERIALS_DIR", str(ROOT / "course-materials"))

from app.db import init_db, get_session, NotebookCell, Question, SourceSpan  # noqa: E402
from app.ingest import ingest_all  # noqa: E402
from app.seed import seed  # noqa: E402


@pytest.fixture(scope="session")
def seeded():
    Path(ROOT / "services" / "api" / "data").mkdir(parents=True, exist_ok=True)
    init_db()
    return seed()


def test_ingest_notebooks(seeded):
    session = get_session()
    assert session.query(SourceSpan).count() >= 50
    assert session.query(NotebookCell).count() >= 50
    dangerous = session.query(NotebookCell).filter_by(dangerous=True).count()
    # requests.post to VSS exists — marked dangerous, never executed
    assert dangerous >= 1
    session.close()


def test_no_execution_counts_required(seeded):
    session = get_session()
    cells = session.query(NotebookCell).all()
    # Clone has null execution counts — still ingested
    assert any(c.execution_count is None for c in cells)
    session.close()


def test_questions_have_sources(seeded):
    session = get_session()
    qs = session.query(Question).all()
    assert len(qs) >= 400
    for q in qs[:50]:
        assert q.source.get("file")
    session.close()
