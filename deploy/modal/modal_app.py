"""Modal FastAPI app — pin to one container while SQLite is the store."""

from __future__ import annotations

import os

import modal

MIN = int(os.environ.get("MODAL_MIN_CONTAINERS", "0"))
MAX = int(os.environ.get("MODAL_MAX_CONTAINERS", "1"))

image = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_dir("services", remote_path="/root/services")
    .add_local_dir("course-materials", remote_path="/root/course-materials")
    .pip_install_from_requirements("services/api/requirements.txt")
)

app = modal.App("modality-twin-academy-api")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("academy-env", required_keys=[])],
    min_containers=MIN,
    max_containers=MAX,
    scaledown_window=300,
    timeout=60 * 30,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    import os
    import sys
    from pathlib import Path

    Path("/root/data").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DATABASE_URL", "sqlite:////root/data/academy.db")
    os.environ.setdefault("COURSE_MATERIALS_DIR", "/root/course-materials")
    sys.path.insert(0, "/root/services/api")
    sys.path.insert(0, "/root/services/twin-engine")
    from app.main import app as inner

    return inner
