"""Simple/expert audio lectures. Shared step structure; glossary only in simple mode."""

from __future__ import annotations

import re
from typing import Any

from .knowledge import CONCEPTS

JARGON_SIMPLE_BLOCKLIST = (
    "backpropagation",
    "logits",
    "tensor parallelism",
    "kv cache",
    "disaggregated",
    "podgang",
    "keda",
)

GLOSSARY = {
    "fusion": "combining two senses so one model can use both",
    "lidar": "a laser rangefinder that measures distance, not color",
    "replica": "another running copy of the model server",
    "chunk": "a short slice of the video the model looks at",
    "projector": "a small network that translates one embedding space into another",
    "embedding": "a list of numbers that stands for a picture, scan, or sentence",
    "caption": "a short text the video model writes about a chunk",
    "graph": "a map of who-did-what-to-what, not just similar sentences",
    "overfit": "memorizing the training set so new examples fail",
    "spectrogram": "a picture of sound: time across, frequency up, loudness as color",
}

SYMBOL_SPOKEN = (
    (re.compile(r"\b(\d+)\s*/\s*(\d+)\b"), r"\1 of \2"),
    (re.compile(r"→|->"), " then "),
    (re.compile(r"(?<![<>])=(?![=])"), " equals "),
    (re.compile(r"(?<!:)//"), " or "),
    (re.compile(r"(?<!:)/(?![/0-9])"), " or "),
    (re.compile(r"\?\."), "?"),
)

HEADING_NUM = re.compile(r"^\d+(?:\.\d+)*\s+")


def humanize_title(title: str) -> str:
    t = HEADING_NUM.sub("", (title or "").strip())
    return re.sub(r"\s+", " ", t)


def speakable(text: str) -> str:
    out = text or ""
    for pat, repl in SYMBOL_SPOKEN:
        out = pat.sub(repl, out)
    out = re.sub(r"\?\.", "?", out)
    return re.sub(r"\s+", " ", out).strip()


def apply_glossary(text: str, used: set[str]) -> str:
    """Lowercase prose matches only; skip proper nouns and existing parentheses; once each."""

    def repl(match: re.Match) -> str:
        word = match.group(0)
        key = word.lower()
        if key in used:
            return word
        if match.start() > 0 and text[match.start() - 1].isupper():
            return word
        # skip if already inside parentheses nearby
        left = text[: match.start()]
        if left.rfind("(") > left.rfind(")"):
            return word
        used.add(key)
        return f"{word} ({GLOSSARY[key]})"

    pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in GLOSSARY) + r")\b", re.I)
    return pattern.sub(repl, text)


def _concept(slug: str) -> dict:
    return next((c for c in CONCEPTS if c["slug"] == slug), CONCEPTS[0])


# Cell ranges must cover 0 .. n-1 inclusive for every notebook.
FRAMES: dict[str, dict[str, Any]] = {
    "00_jupyterlab.ipynb": {
        "title": "JupyterLab and a clean GPU",
        "hook": "Before any fusion math, you share a GPU with leftover kernels.",
        "business": "A forgotten notebook can out-of-memory the assessment and waste classroom time.",
        "simple_model": "Think of the GPU as one whiteboard. If the last class left notes, your new drawing has no room. Reset is janitorial work, not model training.",
        "expert_model": "Labs share device memory. Kernel reset and GPU cache clear prevent allocator fragmentation from prior VSS or training cells. This is operational hygiene, not a performance result.",
        "game_plan": "Orient, run a harmless cell, reset, then leave a clean device for 01a.",
        "remember": "Resetting the kernel is not evidence that a model trained.",
        "dives": ["gpu-memory", "never-execute"],
        "stages": [
            {"title": "Orient", "start": 0, "end": 3, "crux": "This notebook is orientation, not fusion."},
            {"title": "Run and reset", "start": 4, "end": 7, "crux": "A successful cell run is not an ACTUAL_RUN of a multimodal model."},
        ],
        "n_cells": 8,
    },
    "01a_Early_and_Late_Fusion.ipynb": {
        "title": "Early and late fusion",
        "hook": "A camera sees paint. A laser sees distance. The question is when to let those senses talk.",
        "business": "Shipping the wrong fusion wastes sensors: LiDAR spend without color identity, or cameras without metric structure.",
        "simple_model": "Early fusion stacks the two pictures into one thicker picture and trains one student. Late fusion lets each student finish the test, then averages their answers. If the laser cannot see color, stacking too late means the color student never helps the laser student find the right cube.",
        "expert_model": "Early fusion concatenates RGB+XYZA channels into a single CNN (Net in_ch=8). Late fusion freezes or trains unimodal heads and concatenates activations into an MLP. Complementary residuals decide the winner: mixed shapes let LiDAR locate centers; colored cubes make unimodal LiDAR overfit identity.",
        "game_plan": "Convert beams to XYZA, train unimodal baselines, then early and late fusion, and read the error curves as qualitative course results.",
        "remember": "Fusion helps only when the second stream carries a signal the first stream lacks.",
        "dives": ["lidar-xyza", "early-fusion", "late-fusion", "overfitting-lidar"],
        "stages": [
            {"title": "Why two sensors", "start": 0, "end": 8, "crux": "RGB and LiDAR are complementary, not interchangeable."},
            {"title": "XYZA math", "start": 9, "end": 24, "crux": "Negate azimuth and zenith; mask max-range ghosts."},
            {"title": "Unimodal nets", "start": 25, "end": 44, "crux": "Baselines tell you which stream already solves the task."},
            {"title": "Early versus late", "start": 45, "end": 62, "crux": "Late fusion is an ensemble of heads, not mid-network mixing."},
            {"title": "Read the curves", "start": 63, "end": 71, "crux": "Stored outputs are COURSE_SOURCE; a blank cell is not success."},
        ],
        "n_cells": 72,
    },
    "01b_Exploring_Modalities.ipynb": {
        "title": "Audio, CT, and other grids",
        "hook": "A new sensor becomes usable when you turn it into a grid a convolutional net can see.",
        "business": "Hospitals and factories already have CT and microphones; the skill is representation, not buying a new backbone every time.",
        "simple_model": "Sound is a wavy line. A spectrogram is that line drawn as a heatmap so a picture-brain can read it. A CT scan is a loaf of bread: you choose which way to slice.",
        "expert_model": "WAV amplitude at fixed sample_rate; STFT windows yield time×frequency. Nyquist is sample_rate/2. NiBabel NIfTI volumes; U-Net is the cited biomedical segmenter. Axis choice in animate_ct_scan changes the clinical view, not the volume itself.",
        "game_plan": "Hear Nyquist, draw a spectrogram, slice CT, name U-Net, then stop before inventing clinical claims.",
        "remember": "Representation is the first architecture decision.",
        "dives": ["spectrogram", "nyquist", "ct-nifti", "unet"],
        "stages": [
            {"title": "Audio to spectrogram", "start": 0, "end": 14, "crux": "Nyquist is half the sample rate — not a hyperparameter of VSS."},
            {"title": "CT volumes", "start": 15, "end": 27, "crux": "Slicing axis is a view, not a new dataset."},
            {"title": "U-Net mention", "start": 28, "end": 36, "crux": "U-Net is cited for biomedical segmentation, not proven here as an ACTUAL_RUN."},
        ],
        "n_cells": 37,
    },
    "02a_Intermediate_Fusion.ipynb": {
        "title": "When streams must mix in the middle",
        "hook": "Same-shaped cubes, different paint. Geometry cannot name the object.",
        "business": "If identity lives in one sensor and pose in another, late ensembles underperform — you paid for both sensors and threw the interaction away.",
        "simple_model": "Imagine two friends: one feels the shape, one sees the color. If they only talk after writing their own answers, they may never match color to the right cube. Intermediate fusion lets them whisper during the test.",
        "expert_model": "Colored cubes: LiDAR overfits position without identity. Concat stacks mid-level maps; matmul mixes spatial locations (not Hadamard). Early Net(8) and late head-concat are controls. Validation gap is the teaching statistic.",
        "game_plan": "Reproduce the color-critical task, compare four fusion depths, defend concat or matmul with the gap — not a universal winner.",
        "remember": "Intermediate fusion exists because some facts only appear when streams interact.",
        "dives": ["colored-cubes-task", "intermediate-concat", "intermediate-matmul", "overfitting-lidar"],
        "stages": [
            {"title": "The color task", "start": 0, "end": 8, "crux": "LiDAR cannot see paint; low train error is not a solved system."},
            {"title": "Four architectures", "start": 9, "end": 24, "crux": "Name the join: channel stack, head concat, feature concat, or matmul."},
            {"title": "Compare and defend", "start": 25, "end": 36, "crux": "Curves here are qualitative unless you import an ACTUAL_RUN."},
        ],
        "n_cells": 37,
    },
    "02b_Contrastive_Pretraining.ipynb": {
        "title": "CLIP-style pairing without language",
        "hook": "You can pretrain a shared space with photos and their outlines — no sentences required.",
        "business": "A cheaper or private modality can retrieve the other if they share a contrastive space.",
        "simple_model": "Show the model a shoe photo and the shoe's outline. Reward it for putting matching pairs close and strangers far. Later, an outline can find the photo.",
        "expert_model": "FashionMNIST paired with Sobel outlines. Cosine similarities, repeat_interleave versus repeat for the all-pairs matrix, symmetric cross-entropy against identity targets. Temperature scales the logits. This is the same skeleton as CILP in 05.",
        "game_plan": "Build encoders, form the matrix, write symmetric loss, then probe retrieval — do not claim SOTA.",
        "remember": "Contrastive pre-training is a pairing recipe, not a text-only brand name.",
        "dives": ["clip-style", "cosine-similarity", "sobel-outline"],
        "stages": [
            {"title": "Paired modalities", "start": 0, "end": 16, "crux": "The second stream is an outline, not a caption."},
            {"title": "The similarity matrix", "start": 17, "end": 40, "crux": "Diagonal should beat off-diagonal after training."},
            {"title": "Symmetric loss", "start": 41, "end": 63, "crux": "Average both directions of cross-entropy."},
        ],
        "n_cells": 64,
    },
    "03a_Projection.ipynb": {
        "title": "Reuse a frozen model with a projector",
        "hook": "You often cannot retrain the production encoder. You add a translator.",
        "business": "Retaining a frozen head protects a validated model; a small MLP is cheaper than a full finetune and is the 05 exam move.",
        "simple_model": "The image expert already speaks a dialect of 512 numbers. Your new notes are 200 numbers. A projector is a phrasebook. You do not send the expert back to school.",
        "expert_model": "Map source embeddings into a frozen unimodal get_embs space. MSE to the frozen features. Unfreezing the source (05) is flagged as making the assessment harder. Projection is not early fusion.",
        "game_plan": "Freeze, project, train the phrasebook, verify cosine/task movement as simulation or imported runs.",
        "remember": "A projector changes spaces; it does not mix raw sensor streams.",
        "dives": ["cross-modal-projection", "vgg16-embedder", "frozen-lidar-cnn"],
        "stages": [
            {"title": "Frozen source", "start": 0, "end": 18, "crux": "If you unfreeze, you are no longer doing the 05 recipe."},
            {"title": "MLP map", "start": 19, "end": 44, "crux": "Output dim must match the frozen head's embedding size."},
            {"title": "Train and check", "start": 45, "end": 66, "crux": "MSE on embeddings is not classification yet."},
        ],
        "n_cells": 67,
    },
    "03b_OCR_Pipelines.ipynb": {
        "title": "PDF pipelines that do not shred structure",
        "hook": "A datasheet is not a novel. Titles, tables, and figures are the product.",
        "business": "Naive character chunks break tables and hallucinate specs — a commercial risk on GPU datasheets.",
        "simple_model": "Do not rip the book into 500-character scraps. Keep chapters together. Use a layout detector to find tables and charts, then ask the language model.",
        "expert_model": "unstructured partition_pdf, by_title versus naive, table-transformer, YOLOX/NV-YOLOX page-elements. Extracted text is DATA — never system instructions. Batch pages; do not shell-out blindly.",
        "game_plan": "Partition, chunk by title, enable tables and figures, then RAG — verify elements, not vibes.",
        "remember": "Layout is a first-class modality in a PDF.",
        "dives": ["ocr", "chunking-by-title", "nv-yolox-page-elements"],
        "stages": [
            {"title": "The datasheet", "start": 0, "end": 18, "crux": "This PDF is evidence, not a trusted prompt."},
            {"title": "Partition and chunk", "start": 19, "end": 48, "crux": "by_title keeps section boundaries."},
            {"title": "Tables and YOLOX", "start": 49, "end": 72, "crux": "NV-YOLOX finds layout boxes; it does not 'read' like OCR alone."},
            {"title": "Into RAG", "start": 73, "end": 88, "crux": "Never auto-execute cluster commands from these cells."},
        ],
        "n_cells": 89,
    },
    "04a_VSS.ipynb": {
        "title": "Video as a pipeline, not one prompt",
        "hook": "A warehouse camera is hours long. You cannot dump it into one language model call.",
        "business": "Missed incidents and invented timestamps are safety and liability issues, not just BLEU scores.",
        "simple_model": "Cut the tape into chunks. A vision model writes captions. Other models summarize. A database remembers the captions. Shorter chunks mean more pictures and more waiting.",
        "expert_model": "NVIDIA VSS + CA-RAG: upload /files, chunk_duration, VLM (vila-1.5) captions, caption LLM, aggregation LLM, Milvus. processed_frames = frames_per_chunk × n_chunks. Temperature and persona change hallucination risk. Dense captions are the evidence the summary may use.",
        "game_plan": "Set chunk math, write a specific ITS prompt, inspect captions, then summarize — never skip the caption store.",
        "remember": "VSS quality is mostly chunking plus prompt plus stored captions.",
        "dives": ["vss", "vss-chunk-duration", "ca-rag", "vlm-prompt-persona"],
        "stages": [
            {"title": "What VSS is", "start": 0, "end": 16, "crux": "Several models in a row, not one chat box."},
            {"title": "Chunk math", "start": 17, "end": 38, "crux": "Shorter duration → more frames → more detail and latency."},
            {"title": "Prompts and sampling", "start": 39, "end": 62, "crux": "Generic prompts drop timestamps; temperature is not chunk size."},
            {"title": "Captions to summary", "start": 63, "end": 84, "crux": "If the summary is weak, read Milvus captions before blaming the last LLM."},
        ],
        "n_cells": 85,
    },
    "04b_VSS_GraphRAG.ipynb": {
        "title": "When 'similar captions' cannot answer who did what",
        "hook": "Was the worker carrying the box wearing PPE? Similarity search may never join those facts.",
        "business": "Safety Q&A that misses relations is a compliance failure even if captions look fluent.",
        "simple_model": "Vector search finds nearby diary entries. A graph draws arrows: worker wears PPE, worker carries box. Live cameras may only get the diary. Recorded video can get the arrows if you turn chat ingest on.",
        "expert_model": "G-Extraction (LLM → nodes/edges), G-Retriever (Cypher), G-Generation. enable_chat builds the graph. Live streams: Vector-RAG only. Neo4j is not optional decoration for relational questions.",
        "game_plan": "Ask a relational question both ways, inspect retrieved edges, then explain why live is different.",
        "remember": "Graph-RAG is for relations; live streams in this course stay on Vector-RAG.",
        "dives": ["vector-rag", "graph-rag", "enable-chat", "g-retriever"],
        "stages": [
            {"title": "Vector versus graph", "start": 0, "end": 12, "crux": "Same question, different retrieval contract."},
            {"title": "Build and query", "start": 13, "end": 28, "crux": "enable_chat=false means no graph to retrieve."},
            {"title": "Live-stream limit", "start": 29, "end": 39, "crux": "Do not promise Cypher on live VSS."},
        ],
        "n_cells": 40,
    },
    "05_Assessment.ipynb": {
        "title": "CILP: cameras borrowing a LiDAR head",
        "hook": "LiDAR classifiers are expensive to run everywhere. Cameras are cheap. Align, project, freeze.",
        "business": "The commercial story is cost: reuse a validated LiDAR head via contrastive alignment plus a projector — not by pretending RGB is a depth sensor.",
        "simple_model": "Teach a shared space where a photo and a laser picture of the same object sit together. Then a tiny translator lets the photo talk to the already-trained laser grader. Do not send the grader back to school.",
        "expert_model": "CILP = Contrastive Image LiDAR Pre-training. RGB embedder and LiDAR embedder to 200-d, symmetric CE. Projector 200 → lidar_cnn.get_embs. Freeze lidar_cnn and CILP. Gates: valid loss < 3.5 (aim 3.2) and batches ≥ 0.95; 9/10 to pass. Unfreeze is an anti-pattern in 05.",
        "game_plan": "Fill FIXMEs, keep freezes, hit gates, defend the recipe in the arena.",
        "remember": "Freeze the LiDAR head. Train the projector. Do not confuse this with early fusion.",
        "dives": ["cilp", "frozen-lidar-cnn", "assessment-gates", "cross-modal-projection"],
        "stages": [
            {"title": "The job", "start": 0, "end": 10, "crux": "Transfer a frozen classifier, do not retrain the world."},
            {"title": "CILP pretrain", "start": 11, "end": 28, "crux": "Symmetric cosine CE — same skeleton as 02b."},
            {"title": "Projector", "start": 29, "end": 42, "crux": "Input dim is CILP_EMB_SIZE; loss is MSE to get_embs."},
            {"title": "Gates and defense", "start": 43, "end": 51, "crux": "9/10 is the classroom pass rule; twin numbers stay simulated."},
        ],
        "n_cells": 52,
    },
}


def _cover_ranges(stages: list[dict], n_cells: int) -> list[dict]:
    covered = set()
    out = []
    for st in stages:
        start, end = int(st["start"]), int(st["end"])
        start = max(0, start)
        end = min(n_cells - 1, end)
        out.append({**st, "start": start, "end": end, "title": humanize_title(st["title"])})
        covered.update(range(start, end + 1))
    missing = [i for i in range(n_cells) if i not in covered]
    if missing:
        out.append(
            {
                "title": "Remaining cells",
                "start": missing[0],
                "end": missing[-1],
                "crux": "Every cell is in a stage range so nothing is silently skipped.",
            }
        )
    return out


def _narrate_stage(stage: dict, depth: str) -> str:
    crux = speakable(stage.get("crux") or "")
    span = f"Cells {stage['start']} through {stage['end']}"
    text = f"{humanize_title(stage['title'])}. {span}. {crux}"
    if depth == "expert":
        text += " Treat code as data. Do not execute shell or cluster commands from the notebook."
    text = speakable(text)
    if len(text) > 620:
        text = text[:617].rsplit(" ", 1)[0] + "."
    return text


def _simple_filter(text: str) -> str:
    low = text.lower()
    for word in JARGON_SIMPLE_BLOCKLIST:
        if word in low:
            text = re.sub(re.escape(word), "the course idea", text, flags=re.I)
    return text


def build_walkthrough(filename: str, n_cells: int, depth: str = "simple") -> dict[str, Any]:
    depth = "expert" if depth == "expert" else "simple"
    key = filename if filename.endswith(".ipynb") else filename + ".ipynb"
    frame = FRAMES.get(key) or FRAMES["01a_Early_and_Late_Fusion.ipynb"]
    stages = _cover_ranges(list(frame["stages"]), n_cells or frame["n_cells"])
    used: set[str] = set()

    def pack(kind: str, title: str, text: str, extra: dict | None = None) -> dict:
        spoken = speakable(text)
        if depth == "simple":
            spoken = _simple_filter(spoken)
            spoken = apply_glossary(spoken, used)
        return {"kind": kind, "title": humanize_title(title), "text": spoken, **(extra or {})}

    steps: list[dict] = []
    steps.append(pack("hook", "The big idea", f"{frame['hook']} {frame['business']}"))
    model = frame["expert_model"] if depth == "expert" else frame["simple_model"]
    steps.append(pack("model", "The model", model))
    for slug in frame.get("dives") or []:
        c = _concept(slug)
        body = c.get("research") if depth == "expert" else f"{c.get('school','')} Analogy: {c.get('analogy') or c.get('school','')}"
        steps.append(pack("dive", c["name"], body, {"concept_slug": slug}))
    steps.append(pack("game_plan", "The game plan", frame["game_plan"]))
    for st in stages:
        steps.append(
            pack(
                "stage",
                st["title"],
                _narrate_stage(st, depth),
                {"start": st["start"], "end": st["end"], "crux": st.get("crux"), "cells": list(range(st["start"], st["end"] + 1))},
            )
        )
    steps.append(pack("remember", "The one thing to remember", frame["remember"]))

    families: set[str] = set()
    cleaned = []
    for step in steps:
        fam = step["kind"]
        if fam in {"hook", "model", "game_plan", "remember"} and fam in families:
            continue
        families.add(fam) if fam in {"hook", "model", "game_plan", "remember"} else None
        cleaned.append(step)

    return {
        "filename": key,
        "depth": depth,
        "title": humanize_title(frame["title"]),
        "structure": ["hook", "model", "dive", "game_plan", "stage", "remember"],
        "steps": cleaned,
        "stages": stages,
        "n_cells": n_cells or frame["n_cells"],
        "covered_cells": sorted({i for st in stages for i in range(st["start"], st["end"] + 1)}),
        "clip": False,
        "disclaimer": "Not affiliated with or endorsed by NVIDIA. Explanations are original teaching text grounded in your course files.",
    }


WALKTHROUGH_KINDS = ("hook", "model", "dive", "game_plan", "stage", "remember")
