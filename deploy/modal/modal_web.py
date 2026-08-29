"""Modal Next.js standalone server. Requires NEXT_PUBLIC_API_BASE at deploy time."""

from __future__ import annotations

import os
import sys

import modal

API_BASE = os.environ.get("NEXT_PUBLIC_API_BASE", "").rstrip("/")
if not API_BASE:
    sys.exit(
        "NEXT_PUBLIC_API_BASE is unset. Deploy deploy/modal/modal_app.py first, then rerun:\n"
        "  NEXT_PUBLIC_API_BASE=<api URL> MODAL_MIN_CONTAINERS=0 modal deploy deploy/modal/modal_web.py"
    )

MIN = int(os.environ.get("MODAL_MIN_CONTAINERS", "0"))
MAX = int(os.environ.get("MODAL_MAX_CONTAINERS", "1"))

image = (
    modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12")
    .add_local_dir(
        "apps/web",
        remote_path="/app",
        ignore=["node_modules", ".next", "coverage"],
        copy=True,
    )
    .run_commands(
        "cd /app && npm ci || npm install",
        f"cd /app && NEXT_PUBLIC_API_BASE={API_BASE} npm run build",
        "mkdir -p /app/.next/standalone/.next /app/.next/standalone/public",
        "cp -R /app/.next/static /app/.next/standalone/.next/static",
        "if [ -d /app/public ]; then cp -R /app/public /app/.next/standalone/public; fi",
    )
)

app = modal.App("modality-twin-academy-web")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("academy-env", required_keys=[])],
    min_containers=MIN,
    max_containers=MAX,
    scaledown_window=300,
    timeout=60 * 30,
)
@modal.concurrent(max_inputs=100)
@modal.web_server(port=3000)
def web():
    import os
    import subprocess

    os.environ["PORT"] = "3000"
    os.environ["HOSTNAME"] = "0.0.0.0"
    os.environ["NEXT_PUBLIC_API_BASE"] = API_BASE
    subprocess.Popen(["node", "server.js"], cwd="/app/.next/standalone")
