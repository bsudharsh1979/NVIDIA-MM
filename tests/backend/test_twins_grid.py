from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "twin-engine"))
from twin_engine import SUGGESTED_SCENARIOS, TwinState, run_scenario, SCENARIOS


def test_engine_rejects_actual_run_label():
    with pytest.raises(ValidationError):
        TwinState(scenario="fusion-lab", evidence_type="ACTUAL_RUN", metrics={"x": 1})


@pytest.mark.parametrize("scenario,name,controls", [
    (slug, item["name"], item["controls"])
    for slug, items in SUGGESTED_SCENARIOS.items()
    for item in items
])
def test_suggested_scenarios(scenario, name, controls):
    state = run_scenario(scenario, controls)
    assert state.evidence_type == "SIMULATED_RESULT"
    dumped = state.model_dump()
    assert "ACTUAL_RUN" not in str(dumped.get("evidence_type"))
    assert state.notes
    for value in state.metrics.values():
        assert math.isfinite(float(value))


LIDAR_GRID = [
    {"depth": d, "azimuth_deg": a, "zenith_deg": z, "invert_angles": inv, "max_range": 50}
    for d in (5, 15, 25, 40)
    for a in (-30, 0, 45)
    for z in (-10, 0, 20)
    for inv in (True, False)
]


@pytest.mark.parametrize("controls", LIDAR_GRID)
def test_lidar_directionality_grid(controls):
    state = run_scenario("lidar-geometry", controls)
    assert state.evidence_type == "SIMULATED_RESULT"
    if controls["depth"] >= 50:
        assert state.metrics["valid_return"] == 0.0
    else:
        assert state.metrics["valid_return"] == 1.0
    if controls["invert_angles"] and controls["azimuth_deg"] == 0 and controls["zenith_deg"] == 0:
        assert abs(state.metrics["x"]) < 1e-6
        assert abs(state.metrics["y"] - controls["depth"]) < 1e-6


FUSION_GRID = [
    {"dataset": ds, "architecture": arch, "epochs": 12, "rgb_quality": rgb, "lidar_quality": lid}
    for ds in ("colored_cubes", "mixed_shapes")
    for arch in ("rgb", "lidar", "early", "late", "concat", "matmul")
    for rgb, lid in ((0.4, 0.9), (0.9, 0.4))
]


@pytest.mark.parametrize("controls", FUSION_GRID)
def test_fusion_never_actual(controls):
    state = run_scenario("fusion-lab", controls)
    assert state.evidence_type == "SIMULATED_RESULT"
    if controls["dataset"] == "colored_cubes" and controls["architecture"] == "lidar":
        assert state.metrics["overfit_gap"] > 0.3
    if controls["dataset"] == "colored_cubes" and controls["architecture"] == "concat":
        lidar = run_scenario("fusion-lab", {**controls, "architecture": "lidar"})
        assert state.metrics["valid_error"] < lidar.metrics["valid_error"]


VSS_GRID = [
    {"video_length_s": 120, "chunk_duration_s": d, "frames_per_chunk": f, "chunk_overlap_s": 0, "prompt_specificity": p, "temperature": t}
    for d in (5, 10, 20, 60)
    for f in (8, 10)
    for p, t in ((0.2, 0.9), (0.9, 0.1))
]


@pytest.mark.parametrize("controls", VSS_GRID)
def test_vss_chunk_direction(controls):
    state = run_scenario("vss-pipeline", controls)
    assert state.metrics["processed_frames"] > 0
    assert state.evidence_type == "SIMULATED_RESULT"


@pytest.mark.parametrize("enable_chat,mode", [(True, "graph"), (False, "graph"), (True, "vector")])
def test_graph_rag_chat_flag(enable_chat, mode):
    state = run_scenario("graph-rag", {"enable_chat": enable_chat, "mode": mode})
    if mode == "graph" and not enable_chat:
        assert state.metrics.get("graph_available", 1) < 0.5 or "enable_chat" in " ".join(state.notes).lower() or state.warnings
    assert state.evidence_type == "SIMULATED_RESULT"


@pytest.mark.parametrize("freeze", [True, False])
def test_cilp_freeze_direction(freeze):
    state = run_scenario("cilp-assessment", {"freeze_lidar_cnn": freeze, "trained_fraction": 0.9})
    other = run_scenario("cilp-assessment", {"freeze_lidar_cnn": not freeze, "trained_fraction": 0.9})
    if freeze:
        assert state.metrics["finetuned_accuracy"] >= other.metrics["finetuned_accuracy"]
    assert state.evidence_type == "SIMULATED_RESULT"


@pytest.mark.parametrize("chunking", ["naive", "by_title"])
def test_ocr_chunking(chunking):
    state = run_scenario("ocr-pipeline", {"chunking": chunking, "infer_tables": True, "yolox": True})
    assert state.evidence_type == "SIMULATED_RESULT"


@pytest.mark.parametrize("commit,guess,truth", [
    (False, "missing-graph", "missing-graph"),
    (True, "missing-graph", "missing-graph"),
    (True, "long-chunks", "missing-graph"),
    (False, "lidar-overfit", "lidar-overfit"),
])
def test_incident_withholds_until_commit(commit, guess, truth):
    state = run_scenario(
        "incident-diagnosis",
        {"commit": commit, "hypothesis": guess, "ground_truth": truth},
    )
    if not commit:
        assert "ground_truth" not in state.scene
        assert state.metrics["committed"] == 0
    else:
        assert state.scene["ground_truth"] == truth
        assert state.metrics["correct"] == (1.0 if guess == truth else 0.0)
    assert state.evidence_type == "SIMULATED_RESULT"


@pytest.mark.parametrize("pdf", [True, False])
def test_risk_radar_injection(pdf):
    state = run_scenario("risk-radar", {"pdf_as_instructions": pdf})
    if pdf:
        assert state.metrics["prompt_injection_risk"] > 0.5
    assert state.evidence_type == "SIMULATED_RESULT"


@pytest.mark.parametrize("sr", [8000, 16000, 44100, 48000])
def test_nyquist_tracks_sample_rate(sr):
    state = run_scenario("modality-explorer", {"modality": "audio", "sample_rate": sr})
    assert abs(state.metrics["nyquist_hz"] - sr / 2) < 1e-6


@pytest.mark.parametrize("alignment", [0.1, 0.5, 0.9])
def test_contrastive_diagonal_beats_off(alignment):
    state = run_scenario("contrastive-space", {"alignment": alignment, "batch_size": 6})
    if alignment >= 0.5:
        assert state.metrics["diagonal_mean"] > state.metrics["off_diagonal_mean"]


@pytest.mark.parametrize("freeze_source", [True, False])
def test_projection_freeze_flag(freeze_source):
    state = run_scenario("projection-lab", {"freeze_source": freeze_source, "trained_fraction": 0.7})
    assert state.evidence_type == "SIMULATED_RESULT"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_twin_has_four_suggestions(scenario):
    assert len(SUGGESTED_SCENARIOS[scenario]) >= 4
    for item in SUGGESTED_SCENARIOS[scenario]:
        state = run_scenario(scenario, item["controls"])
        assert state.notes
        assert state.evidence_type == "SIMULATED_RESULT"
