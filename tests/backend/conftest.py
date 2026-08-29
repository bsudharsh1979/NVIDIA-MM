import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("DATABASE_URL", "sqlite:///" + str(ROOT / "services" / "api" / "data" / "test.db"))
os.environ.setdefault("COURSE_MATERIALS_DIR", str(ROOT / "course-materials"))


@pytest.fixture(scope="session", autouse=True)
def _data_dir():
    (ROOT / "services" / "api" / "data").mkdir(parents=True, exist_ok=True)
