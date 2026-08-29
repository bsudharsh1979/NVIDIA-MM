from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.experiments import compare_experiments, import_payload
from app.questions import build_questions


def test_simulation_never_labeled_actual_in_questions():
    for q in build_questions():
        src = q.get("source") or {}
        assert src.get("source_type") == "notebook"
        assert src.get("file", "").endswith(".ipynb")
        assert q["explanation"]


def test_question_count_floor():
    qs = build_questions()
    assert len(qs) >= 400
    types = {q["qtype"] for q in qs}
    assert "mcq" in types
    assert "troubleshooting" in types


def test_import_is_actual_run():
    payload = import_payload("json", "demo", 1, '{"ttft_ms": 12.5, "tokens_per_sec": 80}', "a.json")
    assert payload["evidence_type"] == "ACTUAL_RUN"
    assert payload["raw_preserved"] is True
    assert payload["metrics"]["ttft_ms"] == 12.5


def test_confounders_detected():
    cmp_ = compare_experiments(
        {"metadata": {"gpu_count": 1, "concurrency": 8, "cold": True}, "metrics": {"tokens_per_sec": 100}},
        {"metadata": {"gpu_count": 8, "concurrency": 32, "cold": False}, "metrics": {"tokens_per_sec": 400}},
    )
    assert any("gpu_count" in c for c in cmp_["confounders"])
    assert any("concurrency" in c for c in cmp_["confounders"])
    assert "causality" in cmp_


def test_multimodal_confounders_detected():
    cmp_ = compare_experiments(
        {"metadata": {"architecture": "concat", "dataset": "colored_cubes", "freeze_lidar_cnn": True}, "metrics": {"valid_error": 0.24}},
        {"metadata": {"architecture": "lidar", "dataset": "mixed_shapes", "freeze_lidar_cnn": False}, "metrics": {"valid_error": 0.12}},
    )
    assert any("architecture" in c for c in cmp_["confounders"])
    assert any("freeze_lidar_cnn" in c for c in cmp_["confounders"])


def test_notebook_code_not_executed_on_import():
    # Importer stores text; it must not eval
    raw = "os.system('rm -rf /')"
    payload = import_payload("logs", "evil", 1, raw, "x.log")
    assert payload["evidence_type"] == "ACTUAL_RUN"
    assert "rm -rf" in str(payload["parsed"])
