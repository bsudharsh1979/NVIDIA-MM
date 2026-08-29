#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/services/api:$ROOT/services/twin-engine"
export COURSE_MATERIALS_DIR="$ROOT/course-materials"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$ROOT/services/api/data/academy.db}"
mkdir -p "$ROOT/services/api/data"
cd "$ROOT/services/api"
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
