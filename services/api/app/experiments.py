from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

from .db import BenchmarkRun, EvidenceArtifact, Experiment


def import_payload(kind: str, name: str, user_id: int, raw: str, filename: str = "") -> dict:
    """Store ACTUAL_RUN evidence. Never overwrite the original payload."""
    kind = kind.lower()
    parsed, metrics, warnings = _parse(kind, raw, filename)
    return {
        "kind": kind,
        "name": name,
        "filename": filename,
        "metrics": metrics,
        "warnings": warnings,
        "parsed": parsed,
        "evidence_type": "ACTUAL_RUN",
        "raw_preserved": True,
    }


def _parse(kind: str, raw: str, filename: str) -> tuple[Any, dict, list[str]]:
    warnings: list[str] = []
    if kind in {"json", "aiperf", "otel", "prometheus"}:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {"text": raw[:5000]}, {}, ["JSON parse failed; stored as text"]
        metrics = _walk_metrics(data)
        return data, metrics, warnings
    if kind in {"csv", "grafana"}:
        reader = csv.DictReader(io.StringIO(raw))
        rows = list(reader)
        metrics = {}
        if rows:
            for key, value in rows[-1].items():
                try:
                    metrics[key] = float(value)
                except (TypeError, ValueError):
                    pass
        return {"rows": len(rows), "preview": rows[:5]}, metrics, warnings
    if kind in {"kubectl", "k8s-events", "logs"}:
        return {"text": raw[:20000], "lines": raw.count("\n") + 1}, {"lines": float(raw.count("\n") + 1)}, warnings
    return {"text": raw[:20000]}, {}, warnings


def _walk_metrics(obj: Any, prefix: str = "") -> dict[str, float]:
    out: dict[str, float] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[key] = float(v)
            elif isinstance(v, (dict, list)) and len(out) < 80:
                out.update(_walk_metrics(v, key))
    elif isinstance(obj, list) and obj and len(out) < 80:
        out.update(_walk_metrics(obj[0], prefix + "[0]"))
    return out


def compare_experiments(a: dict, b: dict) -> dict:
    meta_a = a.get("metadata") or {}
    meta_b = b.get("metadata") or {}
    confounders = []
    for field in (
        "gpu_type",
        "gpu_count",
        "model",
        "precision",
        "isl",
        "osl",
        "concurrency",
        "engine",
        "warmup",
        "cache_state",
        "architecture",
        "dataset",
        "split",
        "freeze_lidar_cnn",
        "freeze_cilp",
        "chunk_duration_s",
    ):
        if meta_a.get(field) != meta_b.get(field) and (field in meta_a or field in meta_b):
            confounders.append(f"{field} differs: {meta_a.get(field)} vs {meta_b.get(field)}")
    if meta_a.get("cold") != meta_b.get("cold"):
        confounders.append("One run looks cold and the other warm.")
    metrics_a = a.get("metrics") or {}
    metrics_b = b.get("metrics") or {}
    deltas = {}
    for key in set(metrics_a) | set(metrics_b):
        if key in metrics_a and key in metrics_b:
            deltas[key] = metrics_b[key] - metrics_a[key]
    gpu_a = float(meta_a.get("gpu_count") or 1)
    gpu_b = float(meta_b.get("gpu_count") or 1)
    normalized = {}
    for label, metrics, gpu in (("a", metrics_a, gpu_a), ("b", metrics_b, gpu_b)):
        tps = metrics.get("output_tokens_per_sec") or metrics.get("tokens_per_sec")
        rps = metrics.get("requests_per_sec")
        if tps:
            normalized[f"{label}_tokens_per_sec_per_gpu"] = tps / max(gpu, 1)
        if rps:
            normalized[f"{label}_requests_per_sec_per_gpu"] = rps / max(gpu, 1)
    return {
        "confounders": confounders,
        "deltas": deltas,
        "normalized": normalized,
        "evidence_type": "ACTUAL_RUN",
        "causality": "Differences are correlational until controls match. Confounders listed above.",
    }


def explain_experiment(payload: dict) -> dict:
    metrics = payload.get("metrics") or {}
    return {
        "what_happened": {k: v for k, v in metrics.items() if isinstance(v, (int, float))},
        "important_changes": payload.get("deltas") or {},
        "likely_explanations": payload.get("hypotheses")
        or ["Hypotheses only — do not treat correlation as causality."],
        "alternative_explanations": payload.get("confounders") or ["Uncontrolled workload, hardware, or warmup differences."],
        "what_to_check_next": [
            "Match architecture, dataset/split, freeze flags, chunk_duration, and hardware before claiming a winner.",
            "Do not mix SIMULATED_RESULT twin curves with ACTUAL_RUN imports.",
        ],
        "course_connection": "For fusion labs compare architectures on the same Omniverse split; for VSS compare chunk_duration on the same video; for CILP compare projector training with lidar_cnn frozen.",
        "evidence_type": payload.get("evidence_type") or "ACTUAL_RUN",
    }
