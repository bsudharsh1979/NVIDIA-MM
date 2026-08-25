from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "twin-engine"))
from twin_engine import run_scenario, SCENARIOS


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_twins_finite_metrics(scenario):
    state = run_scenario(scenario, {})
    assert state.evidence_type == "SIMULATED_RESULT"
    for key, value in state.metrics.items():
        assert math.isfinite(value), key
        if any(t in key for t in ("ms", "loss", "latency", "error", "frames", "chunks")):
            assert value >= 0


def test_lidar_origin_beam():
    s = run_scenario("lidar-geometry", {"depth": 25, "azimuth_deg": 0, "zenith_deg": 0, "invert_angles": True})
    assert abs(s.metrics["x"]) < 1e-6
    assert abs(s.metrics["y"] - 25) < 1e-6
    assert abs(s.metrics["z"]) < 1e-6
    assert s.metrics["valid_return"] == 1.0


def test_lidar_max_range_invalid():
    s = run_scenario("lidar-geometry", {"depth": 50, "max_range": 50})
    assert s.metrics["valid_return"] == 0.0


def test_vss_shorter_chunk_more_frames():
    a = run_scenario("vss-pipeline", {"video_length_s": 120, "chunk_duration_s": 30, "frames_per_chunk": 10, "chunk_overlap_s": 0})
    b = run_scenario("vss-pipeline", {"video_length_s": 120, "chunk_duration_s": 5, "frames_per_chunk": 10, "chunk_overlap_s": 0})
    assert b.metrics["processed_frames"] > a.metrics["processed_frames"]
    assert b.metrics["relative_latency_s"] > a.metrics["relative_latency_s"]


def test_fusion_lidar_overfit_on_cubes():
    s = run_scenario("fusion-lab", {"dataset": "colored_cubes", "architecture": "lidar", "epochs": 20})
    assert s.metrics["overfit_gap"] > 0.3
    assert s.evidence_type == "SIMULATED_RESULT"


def test_zero_decode_analog_zero_output_tokens_vss():
    s = run_scenario("vss-pipeline", {"video_length_s": 1, "chunk_duration_s": 1, "frames_per_chunk": 1})
    assert s.metrics["chunks"] >= 1
    assert s.metrics["processed_frames"] >= 1


def test_cilp_unfreeze_hurts():
    frozen = run_scenario("cilp-assessment", {"freeze_lidar_cnn": True, "trained_fraction": 0.9})
    unfrozen = run_scenario("cilp-assessment", {"freeze_lidar_cnn": False, "trained_fraction": 0.9})
    assert unfrozen.metrics["finetuned_accuracy"] < frozen.metrics["finetuned_accuracy"]
