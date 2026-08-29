"""Canonical digital-twin state. Web UI and Omniverse consume the same JSON."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

EvidenceType = Literal[
    "COURSE_SOURCE",
    "EXPECTED_RESULT",
    "SIMULATED_RESULT",
    "ACTUAL_RUN",
    "TUTOR_INTERPRETATION",
    "EXTERNAL_RESEARCH",
]


def _finite(value: float, fallback: float = 0.0) -> float:
    if value is None or isinstance(value, bool):
        return fallback
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if math.isnan(number) or math.isinf(number):
        return fallback
    return number


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, _finite(value, lo)))


class TwinState(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str
    evidence_type: EvidenceType = "SIMULATED_RESULT"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    controls: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    series: dict[str, list[float]] = Field(default_factory=dict)
    scene: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _forbid_actual_run(self) -> "TwinState":
        if self.evidence_type == "ACTUAL_RUN":
            raise ValueError("twin engine cannot emit ACTUAL_RUN")
        return self

    def sanitized(self) -> "TwinState":
        unit = {
            "valid_return",
            "rgb_quality",
            "lidar_quality",
            "diagonal_mean",
            "off_diagonal_mean",
            "embedding_cosine",
            "task_accuracy",
            "source_frozen",
            "detail_score",
            "hallucination_risk",
            "graph_available",
            "zero_shot_accuracy",
            "finetuned_accuracy",
            "pass",
            "alignment",
        }
        clean_metrics = {}
        for key, value in self.metrics.items():
            number = _finite(value, 0.0)
            if key in unit or "util" in key:
                number = clamp(number, 0.0, 1.0)
            if any(token in key for token in ("ms", "loss", "latency", "error", "tokens", "frames", "chunks")):
                number = max(0.0, number)
            clean_metrics[key] = round(number, 6)
        self.metrics = clean_metrics
        self.series = {
            name: [max(0.0, _finite(v, 0.0)) for v in values]
            for name, values in self.series.items()
        }
        return self


SCENARIOS = [
    "lidar-geometry",
    "fusion-lab",
    "modality-explorer",
    "contrastive-space",
    "projection-lab",
    "ocr-pipeline",
    "vss-pipeline",
    "graph-rag",
    "cilp-assessment",
    "incident-diagnosis",
    "risk-radar",
]


def run_scenario(scenario: str, controls: dict[str, Any] | None = None) -> TwinState:
    controls = controls or {}
    runners = {
        "lidar-geometry": simulate_lidar,
        "fusion-lab": simulate_fusion,
        "modality-explorer": simulate_modalities,
        "contrastive-space": simulate_contrastive,
        "projection-lab": simulate_projection,
        "ocr-pipeline": simulate_ocr,
        "vss-pipeline": simulate_vss,
        "graph-rag": simulate_graph_rag,
        "cilp-assessment": simulate_cilp,
        "incident-diagnosis": simulate_incident,
        "risk-radar": simulate_risk_radar,
    }
    if scenario not in runners:
        raise ValueError(f"Unknown scenario: {scenario}")
    return runners[scenario](controls).sanitized()


def simulate_lidar(controls: dict[str, Any]) -> TwinState:
    """Educational reconstruction of course LiDAR math (01a cells 16–30)."""
    depth = clamp(float(controls.get("depth", 25.0)), 0.0, 80.0)
    azimuth_deg = float(controls.get("azimuth_deg", 0.0))
    zenith_deg = float(controls.get("zenith_deg", 0.0))
    max_range = clamp(float(controls.get("max_range", 50.0)), 1.0, 200.0)
    invert_angles = bool(controls.get("invert_angles", True))

    azimuth = math.radians(azimuth_deg)
    zenith = math.radians(zenith_deg)
    sign = -1.0 if invert_angles else 1.0
    a_s, z_s = sign * azimuth, sign * zenith

    x = depth * math.sin(a_s) * math.cos(z_s)
    y = depth * math.cos(a_s) * math.cos(z_s)
    z = depth * math.sin(z_s)
    valid = 1.0 if depth < max_range else 0.0

    notes = [
        "Course formula uses sin/cos of negated azimuth and zenith so the point cloud aligns with the RGB image.",
        "If the laser does not return, this sensor family assumes max range — mask those points before visualization.",
    ]
    if not invert_angles:
        notes.append("Without the minus signs the cloud appears rotated relative to RGB (01a).")
    if valid == 0:
        notes.append("This return is at max range and should be masked (a=0).")

    return TwinState(
        scenario="lidar-geometry",
        controls=controls,
        metrics={
            "x": x,
            "y": y,
            "z": z,
            "valid_return": valid,
            "depth": depth,
            "max_range": max_range,
        },
        scene={
            "sensor": {"x": 0.0, "y": 25.0, "z": 0.0},
            "hit": {"x": x, "y": 25.0 - y, "z": z, "valid": valid == 1.0},
            "beam": {"azimuth_deg": azimuth_deg, "zenith_deg": zenith_deg},
        },
        notes=notes,
        warnings=[] if invert_angles else ["Angle convention differs from the 01a notebook default."],
    )


def simulate_fusion(controls: dict[str, Any]) -> TwinState:
    """Relative validation error — educational, not a trained-network measurement."""
    dataset = controls.get("dataset", "colored_cubes")
    architecture = controls.get("architecture", "concat")
    rgb_quality = clamp(float(controls.get("rgb_quality", 0.7)), 0.0, 1.0)
    lidar_quality = clamp(float(controls.get("lidar_quality", 0.85)), 0.0, 1.0)
    color_critical = dataset == "colored_cubes"
    epochs = int(clamp(float(controls.get("epochs", 20)), 1, 80))

    # Course: mixed shapes — LiDAR can locate centers; RGB less necessary.
    # Colored cubes — LiDAR cannot see color and overfits; RGB distinguishes identity.
    base = {
        ("mixed_shapes", "rgb"): (0.45, 0.48),
        ("mixed_shapes", "lidar"): (0.18, 0.22),
        ("mixed_shapes", "early"): (0.20, 0.24),
        ("mixed_shapes", "late"): (0.16, 0.21),
        ("mixed_shapes", "concat"): (0.15, 0.19),
        ("mixed_shapes", "matmul"): (0.14, 0.18),
        ("colored_cubes", "rgb"): (0.42, 0.46),  # ~2 units / object, loss ~6 narrative
        ("colored_cubes", "lidar"): (0.08, 0.72),  # overfit
        ("colored_cubes", "early"): (0.28, 0.36),
        ("colored_cubes", "late"): (0.22, 0.34),
        ("colored_cubes", "concat"): (0.16, 0.24),
        ("colored_cubes", "matmul"): (0.14, 0.22),
    }.get((dataset, architecture), (0.4, 0.5))

    train_err, valid_err = base
    train_err *= 1.15 - 0.3 * (rgb_quality if "rgb" in architecture or architecture in {"early", "late", "concat", "matmul"} else 0)
    valid_err *= 1.2 - 0.25 * lidar_quality if architecture != "rgb" else (1.15 - 0.4 * rgb_quality)
    if color_critical and architecture == "lidar":
        valid_err = max(valid_err, 0.65)
        train_err = min(train_err, 0.12)

    train_curve = [_decay(train_err * 2.2, train_err, i, epochs) for i in range(epochs)]
    valid_curve = [_decay(valid_err * 1.6, valid_err, i, epochs, noise=architecture == "lidar" and color_critical) for i in range(epochs)]

    notes = [
        "SIMULATED relative error curves. They illustrate course qualitative results; they are not stored notebook outputs.",
        "On colored cubes, LiDAR-only cannot bind identity (color) to position — validation error stays high (overfitting).",
        "Intermediate fusion (concat/matmul) mixes streams before the final head so color and geometry can interact.",
    ]
    if architecture == "late":
        notes.append("Late fusion concatenates unimodal heads — like a learned ensemble (01a/02a).")
    if architecture == "early":
        notes.append("Early fusion stacks RGB+XYZA channels and uses one CNN (Net with in_ch=8).")
    if architecture == "matmul":
        notes.append("Matmul mixes spatial locations; Hadamard would only mix aligned cells (02a).")

    return TwinState(
        scenario="fusion-lab",
        controls={**controls, "dataset": dataset, "architecture": architecture, "epochs": epochs},
        metrics={
            "train_error": train_curve[-1],
            "valid_error": valid_curve[-1],
            "overfit_gap": max(0.0, valid_curve[-1] - train_curve[-1]),
            "rgb_quality": rgb_quality,
            "lidar_quality": lidar_quality,
        },
        series={"train_error": train_curve, "valid_error": valid_curve},
        scene={
            "streams": _fusion_streams(architecture),
            "dataset": dataset,
            "color_critical": color_critical,
        },
        notes=notes,
        warnings=["Do not treat these curves as ACTUAL_RUN measurements."] if True else [],
    )


def _decay(start: float, end: float, i: int, n: int, noise: bool = False) -> float:
    t = i / max(n - 1, 1)
    value = start + (end - start) * (1 - math.exp(-3.2 * t))
    if noise:
        value += 0.04 * math.sin(i * 1.7)
    return clamp(value, 0.02, 1.2)


def _fusion_streams(architecture: str) -> dict[str, Any]:
    if architecture == "rgb":
        return {"join": "none", "paths": ["rgb → CNN → positions"]}
    if architecture == "lidar":
        return {"join": "none", "paths": ["xyza → CNN → positions"]}
    if architecture == "early":
        return {"join": "channel_concat", "paths": ["rgb ∥ xyza → CNN(8ch) → positions"]}
    if architecture == "late":
        return {"join": "head_concat", "paths": ["rgb → CNN", "xyza → CNN", "cat heads → MLP"]}
    if architecture == "concat":
        return {"join": "feature_concat", "paths": ["rgb convs", "xyz convs", "cat → MLP"]}
    return {"join": "feature_matmul", "paths": ["rgb convs", "xyz convs", "matmul → MLP"]}


def simulate_modalities(controls: dict[str, Any]) -> TwinState:
    modality = controls.get("modality", "audio")
    sample_rate = int(clamp(float(controls.get("sample_rate", 44100)), 1000, 192000))
    nyquist = sample_rate / 2.0
    ct_axis = int(controls.get("ct_axis", 2))
    notes = {
        "audio": [
            "WAV stores amplitude at a fixed sample rate. FFT windows yield a spectrogram (time × frequency × amplitude).",
            "Nyquist limit: highest reliable frequency is sample_rate/2 (01b).",
        ],
        "ct": [
            "CT volumes are 3D; NiBabel reads NIfTI. U-Net is cited for biomedical segmentation (01b).",
            f"Slicing along axis {ct_axis} matches animate_ct_scan(axis) in 01b.",
        ],
        "rgb": ["RGB is a 2D grid of color; CNNs are the course default analyzer (01a)."],
        "lidar": ["LiDAR returns range along azimuth/zenith; convert to XYZA before CNN (01a)."],
    }.get(modality, ["Unknown modality — staying with course types."])
    return TwinState(
        scenario="modality-explorer",
        controls=controls,
        metrics={"sample_rate": float(sample_rate), "nyquist_hz": nyquist, "ct_axis": float(ct_axis)},
        scene={"modality": modality, "representation": {"audio": "spectrogram", "ct": "nifti_volume", "rgb": "image", "lidar": "xyza"}[modality] if modality in {"audio", "ct", "rgb", "lidar"} else "unknown"},
        notes=notes,
    )


def simulate_contrastive(controls: dict[str, Any]) -> TwinState:
    batch = int(clamp(float(controls.get("batch_size", 6)), 2, 16))
    alignment = clamp(float(controls.get("alignment", 0.82)), 0.0, 1.0)
    temperature = clamp(float(controls.get("temperature", 0.07)), 0.01, 1.0)
    matrix: list[list[float]] = []
    for i in range(batch):
        row = []
        for j in range(batch):
            if i == j:
                row.append(clamp(0.55 + 0.45 * alignment, 0, 1))
            else:
                row.append(clamp((1 - alignment) * 0.35 + 0.05 * ((i + j) % 3), 0, 1))
        matrix.append(row)
    diag = sum(matrix[i][i] for i in range(batch)) / batch
    off = (sum(sum(r) for r in matrix) - diag * batch) / max(batch * batch - batch, 1)
    return TwinState(
        scenario="contrastive-space",
        controls={**controls, "batch_size": batch},
        metrics={
            "diagonal_mean": diag,
            "off_diagonal_mean": off,
            "gap": diag - off,
            "temperature": temperature,
            "batch_size": float(batch),
        },
        scene={"similarity": matrix, "loss": "symmetric_cross_entropy", "ground_truth": "arange(batch)"},
        notes=[
            "CLIP-style: cosine similarities (scaled to [0,1] in 02b) vs identity targets via CrossEntropyLoss.",
            "repeat_interleave vs repeat builds the all-pairs matrix (02b).",
            "Contrastive pre-training is not limited to language–image (02b, 05 CILP).",
        ],
    )


def simulate_projection(controls: dict[str, Any]) -> TwinState:
    frozen = bool(controls.get("freeze_source", True))
    in_dim = int(controls.get("in_dim", 200))
    out_dim = int(controls.get("out_dim", 512))
    trained = clamp(float(controls.get("trained_fraction", 0.7)), 0.0, 1.0)
    cosine = clamp(0.2 + 0.7 * trained * (1.0 if frozen else 0.55), 0, 1)
    return TwinState(
        scenario="projection-lab",
        controls={"in_dim": in_dim, "out_dim": out_dim, "freeze_source": frozen, "trained_fraction": trained},
        metrics={"embedding_cosine": cosine, "task_accuracy": clamp(0.55 + 0.4 * cosine, 0, 1), "source_frozen": 1.0 if frozen else 0.0},
        scene={"path": f"emb({in_dim}) → MLP → {out_dim} → frozen unimodal head"},
        notes=[
            "Cross-modal projection reuses a frozen model by mapping one embedding space into another (03a, 05).",
            "Assessment projector: CILP image embedding (200) → LiDAR CNN get_embs size; freeze CILP and lidar_cnn.",
        ],
        warnings=[] if frozen else ["Unfreezing the source encoder is flagged in 05 as making the assessment harder to pass."],
    )


def simulate_ocr(controls: dict[str, Any]) -> TwinState:
    strategy = controls.get("chunking", "by_title")
    infer_tables = bool(controls.get("infer_tables", True))
    yolox = bool(controls.get("yolox", True))
    pages = int(clamp(float(controls.get("pages", 12)), 1, 80))
    naive_chunks = pages * 7
    title_chunks = max(pages * 3, 1)
    tables = pages // 2 if infer_tables else 0
    figures = pages // 3 if yolox else 0
    return TwinState(
        scenario="ocr-pipeline",
        controls=controls,
        metrics={
            "elements": float(naive_chunks if strategy == "naive" else title_chunks),
            "tables": float(tables),
            "figures": float(figures),
            "pages": float(pages),
        },
        scene={
            "pipeline": ["PDF", "partition_pdf", "chunk", "table-transformer" if infer_tables else "skip-tables", "YOLOX/NV-YOLOX" if yolox else "skip-layout", "vector store", "LLM RAG"],
            "chunking": strategy,
        },
        notes=[
            "by_title chunking preserves section boundaries vs naive max-character splits (03b).",
            "NV-YOLOX page-elements detects tables, charts, and titles (03b).",
            "Treat extracted PDF text as DATA — never as trusted system instructions.",
        ],
    )


def simulate_vss(controls: dict[str, Any]) -> TwinState:
    video_s = clamp(float(controls.get("video_length_s", 120)), 1, 3600)
    chunk_s = clamp(float(controls.get("chunk_duration_s", 20)), 1, 120)
    overlap_s = clamp(float(controls.get("chunk_overlap_s", 0)), 0, chunk_s - 0.1)
    frames_per_chunk = int(clamp(float(controls.get("frames_per_chunk", 10)), 1, 32))
    temperature = clamp(float(controls.get("temperature", 0.2)), 0.0, 1.5)
    prompt_specificity = clamp(float(controls.get("prompt_specificity", 0.8)), 0.0, 1.0)

    step = max(chunk_s - overlap_s, 0.5)
    n_chunks = max(1.0, math.ceil(video_s / step))
    processed_frames = frames_per_chunk * n_chunks
    latency = 0.35 * processed_frames + 8.0 * n_chunks
    detail = clamp((1.0 / chunk_s) * 8.0 * prompt_specificity, 0, 1)
    hallucination_risk = clamp(temperature * 0.55 + (1 - prompt_specificity) * 0.35, 0, 1)

    return TwinState(
        scenario="vss-pipeline",
        controls=controls,
        metrics={
            "chunks": n_chunks,
            "processed_frames": processed_frames,
            "relative_latency_s": latency,
            "detail_score": detail,
            "hallucination_risk": hallucination_risk,
            "chunk_duration_s": chunk_s,
            "video_length_s": video_s,
        },
        scene={
            "pipeline": ["upload /files", "chunk video", "VLM captions (prompt)", "caption summarization LLM", "summary aggregation LLM", "Milvus embeddings"],
            "model": "vila-1.5",
            "formula": "processed_frames = frames_per_chunk * video_length / chunk_size",
        },
        notes=[
            "04a: smaller chunk_duration processes more frames (more detail, slower).",
            "Generic prompts miss timestamps; ITS persona + format instructions improve traffic reports.",
            "Dense captions in Milvus are the evidence the summary can use — inspect them when summaries are weak.",
        ],
        warnings=["SIMULATED latency/detail — not a live VSS cluster."] ,
    )


def simulate_graph_rag(controls: dict[str, Any]) -> TwinState:
    mode = controls.get("mode", "graph")
    query = str(controls.get("query", "Was the worker carrying the box wearing PPE?"))
    enable_chat = bool(controls.get("enable_chat", True))
    entities = [
        {"id": "worker", "type": "Person"},
        {"id": "box", "type": "Object"},
        {"id": "ppe", "type": "Equipment"},
        {"id": "forklift", "type": "Equipment"},
        {"id": "caution_tape", "type": "Object"},
        {"id": "conveyor", "type": "Equipment"},
    ]
    edges = [
        ("worker", "WEARS", "ppe"),
        ("worker", "CARRIES", "box"),
        ("worker", "PLACES", "caution_tape"),
        ("box", "PLACED_ON", "conveyor"),
    ]
    q = query.lower()
    retrieved = []
    for s, rel, t in edges:
        if any(token in q for token in (s, t, rel.lower(), "ppe", "box", "forklift", "tape", "safety")):
            retrieved.append({"from": s, "rel": rel, "to": t})
    if "forklift" in q:
        retrieved.append({"from": "forklift", "rel": "PRESENT_IN", "to": "warehouse"})

    answer = {
        "graph": "Graph-RAG can follow WEARS/CARRIES relations in Neo4j after enable_chat=True ingestion (04b).",
        "vector": "Vector-RAG retrieves top caption chunks from Milvus, reranks, then calls the LLM (04b). Live streams support Vector-RAG only.",
    }[mode if mode in {"graph", "vector"} else "graph"]

    return TwinState(
        scenario="graph-rag",
        controls={"mode": mode, "query": query, "enable_chat": enable_chat},
        metrics={
            "retrieved_edges": float(len(retrieved)),
            "graph_available": 1.0 if enable_chat and mode == "graph" else 0.0,
        },
        scene={"entities": entities, "edges": edges, "retrieved": retrieved, "answer_hint": answer},
        notes=[
            "G-Extraction: LLM turns dense captions into nodes/edges.",
            "G-Retriever: LLM writes Cypher; G-Generation writes the user-facing answer.",
            "Vector-RAG is the only supported method for live stream processing (04b).",
        ],
        warnings=[] if enable_chat else ["enable_chat was false — knowledge graph is not built."],
    )


def simulate_cilp(controls: dict[str, Any]) -> TwinState:
    freeze_lidar = bool(controls.get("freeze_lidar_cnn", True))
    freeze_cilp = bool(controls.get("freeze_cilp", True))
    img_ch = int(controls.get("img_channels", 4))
    lidar_ch = int(controls.get("lidar_channels", 1))
    emb = int(controls.get("cilp_emb", 200))
    projector_out = int(controls.get("projector_out", 512))
    trained = clamp(float(controls.get("trained_fraction", 0.85)), 0.0, 1.0)

    cilp_loss = clamp(3.8 - 1.1 * trained, 0.4, 5.0)
    pre_acc = clamp(0.55 + 0.22 * trained, 0, 1)
    post_acc = clamp(0.70 + 0.28 * trained, 0, 1)
    if not freeze_lidar or not freeze_cilp:
        post_acc *= 0.72
        cilp_loss += 0.4

    pass_cilp = cilp_loss < 3.5
    pass_acc = post_acc >= 0.95
    points = (5 if pass_cilp else 0) + (5 if pass_acc else int(post_acc * 5))
    points = int(clamp(points, 0, 10))

    return TwinState(
        scenario="cilp-assessment",
        controls=controls,
        metrics={
            "cilp_valid_loss": cilp_loss,
            "zero_shot_accuracy": pre_acc,
            "finetuned_accuracy": post_acc,
            "points": float(points),
            "pass": 1.0 if points >= 9 else 0.0,
        },
        scene={
            "pipeline": [
                f"RGB Embedder({img_ch} ch) → {emb}-d",
                f"LiDAR Embedder({lidar_ch} ch) → {emb}-d",
                "symmetric CE on cosine matrix",
                f"projector {emb} → {projector_out}",
                "frozen lidar_cnn classifier",
            ],
            "fixes": {
                "cos": "nn.CosineSimilarity",
                "repeat": "repeat_interleave / repeat",
                "loss": "(loss_img(logits_per_img, gt) + loss_lidar(logits_per_lidar, gt))/2",
                "projector_in": "CILP_EMB_SIZE (200)",
                "projector_loss": "MSELoss",
                "embedder_for_rgb": "CILP_model.img_embedder",
            },
        },
        notes=[
            "CILP = Contrastive Image LiDAR Pre-training (05) — CLIP analog for RGB↔LiDAR.",
            "Assessment: CILP valid loss < 3.5 (aim 3.2) and five batches ≥ 0.95 accuracy; 9/10 to pass.",
            "Do not unfreeze lidar_cnn (05 explicitly warns this makes the assessment harder).",
        ],
        warnings=[] if freeze_lidar else ["lidar_cnn unfrozen — course says this risks failing the assessment."],
    )


INCIDENT_CAUSES = ("missing-graph", "long-chunks", "lidar-overfit", "unfrozen-head", "naive-chunks")


def simulate_incident(controls: dict[str, Any]) -> TwinState:
    """Symptoms first. Ground truth withheld until the learner commits a cause."""
    truth = str(controls.get("ground_truth") or "missing-graph")
    if truth not in INCIDENT_CAUSES:
        truth = "missing-graph"
    committed = bool(controls.get("commit"))
    guess = str(controls.get("hypothesis") or "")
    symptoms = {
        "missing-graph": {"ppe_answer": 0.15, "caption_hit": 0.8, "graph_edges": 0.0},
        "long-chunks": {"ppe_answer": 0.4, "caption_hit": 0.35, "graph_edges": 0.6},
        "lidar-overfit": {"ppe_answer": 0.5, "caption_hit": 0.5, "valid_error": 0.7},
        "unfrozen-head": {"ppe_answer": 0.45, "finetuned_accuracy": 0.62},
        "naive-chunks": {"ppe_answer": 0.4, "table_integrity": 0.2},
    }[truth]
    notes = ["Symptoms only until you commit a diagnosis. This twin never emits ACTUAL_RUN."]
    if committed:
        notes.append(f"Ground truth: {truth}. Your hypothesis: {guess or 'none'}.")
        notes.append("Correct" if guess == truth else "Mismatch — inspect the withheld leading signal.")
    else:
        notes.append("Ground truth withheld. Commit before the reveal.")
    metrics = {k: float(v) for k, v in symptoms.items()}
    metrics["committed"] = 1.0 if committed else 0.0
    metrics["correct"] = 1.0 if committed and guess == truth else 0.0
    scene = {"symptoms": symptoms, "options": list(INCIDENT_CAUSES)}
    if committed:
        scene["ground_truth"] = truth
    return TwinState(
        scenario="incident-diagnosis",
        controls={k: v for k, v in controls.items() if k != "ground_truth" or committed},
        metrics=metrics,
        scene=scene,
        notes=notes,
        warnings=[] if committed else ["Diagnosis hidden until commit."],
    )


def simulate_risk_radar(controls: dict[str, Any]) -> TwinState:
    rgb_q = clamp(float(controls.get("rgb_quality", 0.7)), 0, 1)
    lidar_q = clamp(float(controls.get("lidar_quality", 0.85)), 0, 1)
    chunk = clamp(float(controls.get("chunk_duration_s", 20)), 1, 120)
    enable_chat = bool(controls.get("enable_chat", True))
    freeze = bool(controls.get("freeze_lidar_cnn", True))
    pdf_instr = bool(controls.get("pdf_as_instructions", False))
    scores = {
        "identity_risk": clamp(0.85 - rgb_q + (0.25 if lidar_q > 0.9 else 0), 0, 1),
        "recall_risk": clamp(chunk / 80.0, 0, 1),
        "relation_risk": 0.0 if enable_chat else 0.9,
        "assessment_risk": 0.15 if freeze else 0.8,
        "prompt_injection_risk": 0.95 if pdf_instr else 0.1,
    }
    top = max(scores, key=scores.get)
    return TwinState(
        scenario="risk-radar",
        controls=controls,
        metrics={**scores, "top_risk": float(list(scores.keys()).index(top))},
        scene={"top": top, "scores": scores},
        notes=[
            f"Highest simulated operational risk: {top}.",
            "Scores are educational priors, not production telemetry.",
        ],
        warnings=["SIMULATED_RESULT — not a live SOC feed."],
    )


SUGGESTED_SCENARIOS: dict[str, list[dict[str, Any]]] = {
    "lidar-geometry": [
        {"name": "origin-beam", "controls": {"depth": 25, "azimuth_deg": 0, "zenith_deg": 0, "invert_angles": True}},
        {"name": "no-invert", "controls": {"depth": 25, "azimuth_deg": 30, "zenith_deg": 10, "invert_angles": False}},
        {"name": "max-range", "controls": {"depth": 50, "max_range": 50}},
        {"name": "steep-zenith", "controls": {"depth": 10, "zenith_deg": 40, "invert_angles": True}},
    ],
    "fusion-lab": [
        {"name": "lidar-overfit-cubes", "controls": {"dataset": "colored_cubes", "architecture": "lidar"}},
        {"name": "need-intermediate", "controls": {"dataset": "colored_cubes", "architecture": "concat"}},
        {"name": "matmul", "controls": {"dataset": "colored_cubes", "architecture": "matmul"}},
        {"name": "shapes-lidar", "controls": {"dataset": "mixed_shapes", "architecture": "lidar"}},
    ],
    "modality-explorer": [
        {"name": "audio", "controls": {"modality": "audio", "sample_rate": 44100}},
        {"name": "low-sr", "controls": {"modality": "audio", "sample_rate": 8000}},
        {"name": "ct", "controls": {"modality": "ct", "ct_axis": 2}},
        {"name": "lidar", "controls": {"modality": "lidar"}},
    ],
    "contrastive-space": [
        {"name": "aligned", "controls": {"alignment": 0.9, "batch_size": 6}},
        {"name": "collapsed", "controls": {"alignment": 0.1, "batch_size": 6}},
        {"name": "hot", "controls": {"temperature": 0.4, "alignment": 0.7}},
        {"name": "batch8", "controls": {"batch_size": 8, "alignment": 0.8}},
    ],
    "projection-lab": [
        {"name": "frozen", "controls": {"freeze_source": True, "trained_fraction": 0.8}},
        {"name": "unfreeze-source", "controls": {"freeze_source": False, "trained_fraction": 0.8}},
        {"name": "wide", "controls": {"in_dim": 200, "out_dim": 512}},
        {"name": "untrained", "controls": {"trained_fraction": 0.05}},
    ],
    "ocr-pipeline": [
        {"name": "by-title", "controls": {"chunking": "by_title", "infer_tables": True, "yolox": True}},
        {"name": "naive-chunk", "controls": {"chunking": "naive"}},
        {"name": "no-tables", "controls": {"infer_tables": False}},
        {"name": "no-yolox", "controls": {"yolox": False}},
    ],
    "vss-pipeline": [
        {"name": "default", "controls": {"chunk_duration_s": 20, "video_length_s": 120}},
        {"name": "long-chunks", "controls": {"chunk_duration_s": 60, "video_length_s": 120}},
        {"name": "short-chunks", "controls": {"chunk_duration_s": 5, "video_length_s": 120}},
        {"name": "vague-prompt", "controls": {"prompt_specificity": 0.1, "temperature": 0.9}},
    ],
    "graph-rag": [
        {"name": "ppe", "controls": {"mode": "graph", "enable_chat": True}},
        {"name": "no-graph", "controls": {"mode": "graph", "enable_chat": False}},
        {"name": "live-vector", "controls": {"mode": "vector", "enable_chat": True}},
        {"name": "forklift", "controls": {"query": "Is there a forklift near the tape?"}},
    ],
    "cilp-assessment": [
        {"name": "pass-path", "controls": {"freeze_lidar_cnn": True, "freeze_cilp": True, "trained_fraction": 0.95}},
        {"name": "unfreeze-hurt", "controls": {"freeze_lidar_cnn": False, "trained_fraction": 0.95}},
        {"name": "undertrained", "controls": {"trained_fraction": 0.2}},
        {"name": "wide-emb", "controls": {"cilp_emb": 256}},
    ],
    "incident-diagnosis": [
        {"name": "ppe-miss", "controls": {"ground_truth": "missing-graph", "commit": False}},
        {"name": "commit-wrong", "controls": {"ground_truth": "missing-graph", "hypothesis": "long-chunks", "commit": True}},
        {"name": "commit-right", "controls": {"ground_truth": "missing-graph", "hypothesis": "missing-graph", "commit": True}},
        {"name": "lidar-case", "controls": {"ground_truth": "lidar-overfit", "commit": False}},
    ],
    "risk-radar": [
        {"name": "prompt-inject", "controls": {"pdf_as_instructions": True}},
        {"name": "evidence-mix", "controls": {"chunk_duration_s": 10}},
        {"name": "gpu-hold", "controls": {"enable_chat": True}},
        {"name": "no-chat", "controls": {"enable_chat": False}},
    ],
}
