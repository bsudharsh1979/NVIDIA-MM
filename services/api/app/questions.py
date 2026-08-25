"""Source-grounded question bank. Generated per concept × type — not one giant LLM dump."""

from __future__ import annotations

from .knowledge import CONCEPTS, MISCONCEPTIONS

BLOOMS = {
    "recall": "recall",
    "application": "apply",
    "troubleshooting": "diagnose",
    "compare": "compare",
    "architecture": "design",
    "notebook": "apply",
    "assessment": "defend",
}


def build_questions() -> list[dict]:
    questions: list[dict] = []
    questions.extend(_handcrafted())
    for concept in CONCEPTS:
        questions.extend(_concept_family(concept))
    questions.extend(_code_fill_fixmes())
    questions.extend(_sequence_and_design())
    # Dedup by prompt
    seen = set()
    unique = []
    for q in questions:
        key = q["prompt"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(q)
    return unique


def _q(
    slug: str,
    qtype: str,
    bloom: str,
    difficulty: int,
    concept: str,
    prompt: str,
    options: list[str],
    answer: str,
    explanation: str,
    source: dict,
    misconception: str = "",
) -> dict:
    return {
        "slug": slug[:170],
        "qtype": qtype,
        "bloom": bloom,
        "difficulty": difficulty,
        "concept_slug": concept,
        "prompt": prompt,
        "options": options,
        "answer": answer,
        "explanation": explanation,
        "source": source,
        "misconception_slug": misconception,
        "validated": True,
    }


def _src(file: str, cell: int) -> dict:
    return {"source_type": "notebook", "file": file, "cell_index": cell}


def _handcrafted() -> list[dict]:
    s01a = "01a_Early_and_Late_Fusion.ipynb"
    s02a = "02a_Intermediate_Fusion.ipynb"
    s02b = "02b_Contrastive_Pretraining.ipynb"
    s03a = "03a_Projection.ipynb"
    s03b = "03b_OCR_Pipelines.ipynb"
    s04a = "04a_VSS.ipynb"
    s04b = "04b_VSS_GraphRAG.ipynb"
    s05 = "05_Assessment.ipynb"
    items = []

    items.append(
        _q(
            "recall-xyza-x",
            "mcq",
            "recall",
            2,
            "lidar-xyza",
            "In notebook 01a, with negated angles, which expression is used for the LiDAR X coordinate?",
            [
                "depth * sin(-azimuth[:, None]) * cos(-zenith[None, :])",
                "depth * cos(-azimuth[:, None]) * cos(-zenith[None, :])",
                "depth * sin(-zenith[None, :])",
                "depth * tan(azimuth) * zenith",
            ],
            "depth * sin(-azimuth[:, None]) * cos(-zenith[None, :])",
            "01a get_torch_xyza: x uses sin(-azimuth) * cos(-zenith); y uses two cosines; z uses sin(-zenith).",
            _src(s01a, 40),
        )
    )
    items.append(
        _q(
            "recall-max-range",
            "mcq",
            "recall",
            1,
            "max-range-mask",
            "How does 01a mark a LiDAR return as valid in get_torch_xyza?",
            [
                "a = 1 where lidar_depth < 50 else 0",
                "a = lidar_depth / max(lidar_depth)",
                "a is the alpha channel of the RGB PNG",
                "a is always 1",
            ],
            "a = 1 where lidar_depth < 50 else 0",
            "torch.where(lidar_depth < 50.0, ones, zeros).",
            _src(s01a, 40),
        )
    )
    items.append(
        _q(
            "recall-late-fusion-def",
            "mcq",
            "recall",
            1,
            "late-fusion",
            "What does the course call late fusion?",
            [
                "Analyze each modality separately and combine near the output (like an ensemble of heads)",
                "Concatenate raw RGB and XYZA channels before the first conv",
                "Multiply feature maps with torch.matmul",
                "Train only the LiDAR net",
            ],
            "Analyze each modality separately and combine near the output (like an ensemble of heads)",
            "01a cell 59 defines late fusion this way.",
            _src(s01a, 59),
        )
    )
    items.append(
        _q(
            "recall-early-fusion-ch",
            "mcq",
            "recall",
            2,
            "early-fusion",
            "Early fusion in 01a instantiates Net with how many input channels, and why?",
            [
                "8 — torch.cat of 4-ch RGB and 4-ch XYZA on the channel dimension",
                "3 — RGB only",
                "1 — LiDAR depth only",
                "9 — one channel per position target",
            ],
            "8 — torch.cat of 4-ch RGB and 4-ch XYZA on the channel dimension",
            "get_mm_early_inputs concatenates dim=1; mm_early_net = Net(8).",
            _src(s01a, 64),
        )
    )
    items.append(
        _q(
            "apply-cubes-lidar",
            "mcq",
            "apply",
            3,
            "colored-cubes-task",
            "On the red/green/blue cubes dataset, why does a LiDAR-only model overfit?",
            [
                "LiDAR cannot observe color, so it cannot bind identity to position and memorizes the train set",
                "The CNN has too few parameters",
                "MSE cannot regress coordinates",
                "Omniverse units are in feet, so loss is mis-scaled",
            ],
            "LiDAR cannot observe color, so it cannot bind identity to position and memorizes the train set",
            "02a: train loss <1, valid >8; RGB valid ~6 (~2 units/object).",
            _src(s02a, 7),
            "lidar-sees-color",
        )
    )
    items.append(
        _q(
            "compare-hadamard-matmul",
            "mcq",
            "compare",
            3,
            "intermediate-matmul",
            "Why does 02a prefer torch.matmul over a Hadamard product for intermediate fusion?",
            [
                "Matmul lets different spatial locations interact; Hadamard only multiplies aligned cells",
                "Hadamard is illegal for square tensors",
                "Matmul reduces RGB to 1 channel",
                "Hadamard requires unfreezing ImageNet",
            ],
            "Matmul lets different spatial locations interact; Hadamard only multiplies aligned cells",
            "02a cell 28 states this explicitly.",
            _src(s02a, 28),
            "matmul-is-hadamard",
        )
    )
    items.append(
        _q(
            "recall-cosine",
            "short_answer",
            "recall",
            2,
            "cosine-similarity",
            "Write the cosine similarity formula used in 02b for two vectors p1 and p2.",
            [],
            "dot(p1,p2)/(norm(p1)*norm(p2))",
            "numpy.dot / product of L2 norms.",
            _src(s02b, 26),
        )
    )
    items.append(
        _q(
            "notebook-clip-loss",
            "fill_fixme",
            "apply",
            4,
            "clip-style",
            "In 02b get_CLIP_loss, total_loss averages which two CrossEntropyLoss terms?",
            [
                "loss_base(logits_per_base, ground_truth) and loss_outline(logits_per_outline, ground_truth)",
                "MSE(base, outline) and MAE(base, outline)",
                "Only loss_base on class labels 0–9 (FashionMNIST classes)",
                "KL(base || outline)",
            ],
            "loss_base(logits_per_base, ground_truth) and loss_outline(logits_per_outline, ground_truth)",
            "ground_truth is arange(BATCH_SIZE), not clothing class ids — contrastive pairing, not 10-way class CE.",
            _src(s02b, 42),
            "contrastive-is-classification-of-classes",
        )
    )
    items.append(
        _q(
            "recall-vss-formula",
            "mcq",
            "recall",
            2,
            "vss-chunk-duration",
            "For a 120 s video, 5 s chunks, 10 frames per chunk, how many frames does 04a say are processed?",
            ["240", "120", "10", "5"],
            "240",
            "N_chunks = 120/5 = 24; frames = 10*24 = 240.",
            _src(s04a, 60),
        )
    )
    items.append(
        _q(
            "apply-vss-detail",
            "mcq",
            "apply",
            3,
            "vss-chunk-duration",
            "You need to catch a car speeding through an intersection. What chunk_duration change does 04a recommend, and what is the cost?",
            [
                "Shorter chunks → more frames processed → more detail, higher latency",
                "Longer chunks → more frames → faster and more detailed",
                "Set temperature=0; chunk size is irrelevant",
                "Increase max_tokens only",
            ],
            "Shorter chunks → more frames processed → more detail, higher latency",
            "04a explicitly uses the speeding-car example.",
            _src(s04a, 60),
            "longer-chunks-always-better",
        )
    )
    items.append(
        _q(
            "recall-live-stream-rag",
            "mcq",
            "recall",
            2,
            "vector-rag",
            "According to 04b, which Q&A method is supported for live stream processing?",
            ["Vector-RAG only", "Graph-RAG only", "Both equally", "Cypher without Milvus"],
            "Vector-RAG only",
            "Opening of 04b.",
            _src(s04b, 1),
            "graph-rag-for-live-stream",
        )
    )
    items.append(
        _q(
            "architecture-graph-rag",
            "sequence",
            "design",
            4,
            "graph-rag",
            "Order the Graph-RAG stages as taught in 04b.",
            ["G-Extraction", "G-Retriever", "G-Generation"],
            "G-Extraction|G-Retriever|G-Generation",
            "Index graph from captions, Cypher retrieve, then generate the answer.",
            _src(s04b, 18),
        )
    )
    items.append(
        _q(
            "assess-cilp-loss",
            "mcq",
            "defend",
            5,
            "assessment-gates",
            "What CILP validation-loss gate does 05 state, and what in-notebook target does it suggest for server re-eval?",
            [
                "Below 3.5 on the server; try to reach 3.2 in the notebook",
                "Below 0.01 cross-entropy",
                "Accuracy 3.5%",
                "Any loss if RGB accuracy is 50%",
            ],
            "Below 3.5 on the server; try to reach 3.2 in the notebook",
            "5 points for CILP loss; plus 5 batches at >0.95 acc; 9/10 to pass.",
            _src(s05, 46),
        )
    )
    items.append(
        _q(
            "assess-unfreeze",
            "mcq",
            "defend",
            4,
            "frozen-lidar-cnn",
            "05 loads lidar_cnn and comments 'Do not unfreeze'. Why is that the assessment design?",
            [
                "The task is to reuse the frozen LiDAR classifier via CILP + projector, not to retrain the CNN on RGB",
                "Unfreezing is illegal in PyTorch",
                "The CNN has no gradients even if unfrozen",
                "RGB images have 1 channel already",
            ],
            "The task is to reuse the frozen LiDAR classifier via CILP + projector, not to retrain the CNN on RGB",
            "Cell 8 warning; RGB2LiDARClassifier uses projector + frozen head.",
            _src(s05, 8),
            "unfreeze-to-pass",
        )
    )
    items.append(
        _q(
            "ocr-by-title",
            "mcq",
            "apply",
            3,
            "chunking-by-title",
            "Why does 03b prefer chunking_strategy='by_title' over naive max-character splits?",
            [
                "Section boundaries stay intact, producing more semantically distinct chunks for RAG",
                "It always yields fewer than 3 chunks",
                "Tesseract requires by_title",
                "It disables OCR",
            ],
            "Section boundaries stay intact, producing more semantically distinct chunks for RAG",
            "03b section 3.2.",
            _src(s03b, 12),
        )
    )
    items.append(
        _q(
            "nv-yolox-labels",
            "multiple_select",
            "recall",
            2,
            "nv-yolox-page-elements",
            "Which page-element labels does NV-YOLOX detect in 03b?",
            ["table", "chart", "title", "paragraph", "footnote"],
            "table|chart|title",
            "Course: tables, charts (bar/line/pie), titles (page/section/table/chart titles).",
            _src(s03b, 41),
        )
    )
    items.append(
        _q(
            "vss-inspect-milvus",
            "troubleshooting",
            "diagnose",
            4,
            "milvus-captions",
            "A VSS traffic summary never mentions a collision you can see in the video. What should you inspect first according to 04a?",
            [
                "Dense captions stored in the Milvus collection for that summary id — if the VLM missed it, aggregation cannot invent it",
                "Only raise temperature",
                "Only Neo4j WEARS edges",
                "Reinstall JupyterLab",
            ],
            "Dense captions stored in the Milvus collection for that summary id — if the VLM missed it, aggregation cannot invent it",
            "04a 4.4.1 and prompt section.",
            _src(s04a, 44),
            "aggregation-prompt-creates-new-facts",
        )
    )
    items.append(
        _q(
            "enable-chat",
            "mcq",
            "apply",
            3,
            "enable-chat",
            "In 04b process_video, which flag builds the knowledge graph for Q&A?",
            ["enable_chat: True", "media_type: graph", "purpose: neo4j", "chunk_duration: 0"],
            "enable_chat: True",
            "summarize payload includes enable_chat True; summarize may be False.",
            _src(s04b, 12),
        )
    )
    items.append(
        _q(
            "cilp-repeat",
            "fill_fixme",
            "apply",
            4,
            "cilp",
            "In 05 ContrastivePretraining.forward, which pair of tensor ops builds the all-pairs comparison (as in 02b)?",
            [
                "img_emb.repeat_interleave(len(img_emb), dim=0) and lidar_emb.repeat(len(lidar_emb), 1)",
                "torch.stack and torch.cat on class_idx",
                "F.interpolate both to 224",
                "vgg16.features on both",
            ],
            "img_emb.repeat_interleave(len(img_emb), dim=0) and lidar_emb.repeat(len(lidar_emb), 1)",
            "FIXME cells in 05 point back to 02b.",
            _src(s05, 20),
        )
    )
    items.append(
        _q(
            "mse-pythagoras",
            "mcq",
            "recall",
            2,
            "mse-as-distance",
            "Why does 01a say MSE is acceptable for position regression?",
            [
                "MSE is Pythagoras without the square root; minimizing MSE also minimizes RMSE",
                "MSE is the only loss that works on GPUs",
                "MSE ignores large errors",
                "MSE classifies cubes vs spheres",
            ],
            "MSE is Pythagoras without the square root; minimizing MSE also minimizes RMSE",
            "01a cell 50.",
            _src(s01a, 50),
        )
    )
    items.append(
        _q(
            "nyquist",
            "mcq",
            "recall",
            1,
            "nyquist",
            "01b: the highest frequency that can be reliably captured is…",
            ["Half the sampling frequency (Nyquist)", "Twice the sampling frequency", "The WAV bit depth", "Always 44.1 kHz"],
            "Half the sampling frequency (Nyquist)",
            "01b audio section.",
            _src("01b_Exploring_Modalities.ipynb", 7),
        )
    )
    items.append(
        _q(
            "prompt-three-part",
            "mcq",
            "apply",
            3,
            "vlm-prompt-persona",
            "04a recommends a three-part VLM prompt. Which trio?",
            ["Persona, details, format", "Temperature, top_p, max_tokens", "Milvus, Neo4j, Cypher", "Prefill, decode, KV"],
            "Persona, details, format",
            "Intelligent traffic system example.",
            _src(s04a, 48),
        )
    )
    items.append(
        _q(
            "expected-vs-actual",
            "mcq",
            "recall",
            2,
            "evidence-types",
            "The notebooks say colored-cube RGB validation loss is about 6, but this clone has no CSV outputs. How should the academy label that number?",
            ["EXPECTED_RESULT (course narrative, not a stored run here)", "ACTUAL_RUN", "EXTERNAL_RESEARCH", "It should be hidden"],
            "EXPECTED_RESULT (course narrative, not a stored run here)",
            "Integrity rule: do not launder notebook claims as measured evidence.",
            _src(s02a, 7),
            "simulation-is-actual",
        )
    )
    items.append(
        _q(
            "distance-image-not-used",
            "mcq",
            "recall",
            2,
            "rgb-camera",
            "01a shows Omniverse distance images. Are they used in the multimodal nets?",
            [
                "No — few real instruments capture that dense distance image; it is for verification",
                "Yes — they replace LiDAR",
                "Yes — they are the fourth RGB channel",
                "They are the assessment labels",
            ],
            "No — few real instruments capture that dense distance image; it is for verification",
            "01a 1.1.2.",
            _src(s01a, 12),
        )
    )
    items.append(
        _q(
            "late-net-params",
            "mcq",
            "compare",
            3,
            "late-fusion",
            "02a notes LateNet is not a perfectly fair comparison to EarlyNet because…",
            [
                "Two Nets ≈ twice the parameters, so it also trains slower",
                "LateNet cannot use GPUs",
                "EarlyNet uses Transformers",
                "LateNet outputs 18 positions",
            ],
            "Two Nets ≈ twice the parameters, so it also trains slower",
            "02a 2.2.2.",
            _src(s02a, 18),
            "more-parameters-always-better",
        )
    )
    items.append(
        _q(
            "vss-upload",
            "mcq",
            "apply",
            2,
            "vss",
            "When posting a video to VSS /files, which purpose and media_type does 04a use?",
            ["purpose=vision, media_type=video", "purpose=rag, media_type=mp4", "purpose=train, media_type=tensor", "purpose=chat, media_type=graph"],
            "purpose=vision, media_type=video",
            "Multipart form on /files.",
            _src(s04a, 20),
        )
    )
    items.append(
        _q(
            "chat-endpoint",
            "mcq",
            "recall",
            2,
            "graph-rag",
            "After ingest, 04b asks questions via which endpoint?",
            ["/chat/completions", "/summarize only", "/files", "/health/ready"],
            "/chat/completions",
            "qna() helper.",
            _src(s04b, 15),
        )
    )
    items.append(
        _q(
            "projector-loss",
            "fill_fixme",
            "apply",
            4,
            "cross-modal-projection",
            "05 get_projector_loss should compare pred_lidar_embs to lidar_cnn.get_embs with which loss (hint: 03a §3.2)?",
            ["MSELoss", "CrossEntropyLoss", "BCEWithLogitsLoss", "CTCLoss"],
            "MSELoss",
            "Projection matches embeddings, not class logits. Classification uses BCEWithLogits later.",
            _src(s05, 33),
        )
    )
    items.append(
        _q(
            "rgb2lidar-embedder",
            "fill_fixme",
            "apply",
            4,
            "cilp",
            "RGB2LiDARClassifier should encode images with which CILP module?",
            ["CILP_model.img_embedder", "CILP_model.lidar_embedder", "lidar_cnn.conv1", "VGG16.features"],
            "CILP_model.img_embedder",
            "We classify RGB, so the image embedder; projector then LiDAR head.",
            _src(s05, 37),
        )
    )
    items.append(
        _q(
            "zero-shot-acc",
            "mcq",
            "recall",
            3,
            "assessment-gates",
            "Before fine-tuning RGB2LiDARClassifier, 05 says validation accuracy should already be above…",
            ["0.70", "0.95", "0.10", "3.2"],
            "0.70",
            "Then 5 epochs should exceed 0.95.",
            _src(s05, 41),
        )
    )
    items.append(
        _q(
            "omniverse-units",
            "mcq",
            "recall",
            2,
            "omniverse-sdg",
            "02a: Omniverse position units are…",
            [
                "Relative (not inherently feet or cm); many DCC apps treat 1 unit ≈ 1 meter",
                "Always millimeters",
                "Always GPS degrees",
                "Tokens",
            ],
            "Relative (not inherently feet or cm); many DCC apps treat 1 unit ≈ 1 meter",
            "02a dataset discussion.",
            _src(s02a, 7),
        )
    )
    items.append(
        _q(
            "sensor-at-25",
            "mcq",
            "application",
            3,
            "lidar-xyza",
            "LiDAR sat at world (0,25,0) with objects near origin. If math is right, point-cloud Y should be roughly…",
            ["25 units away on average", "0", "50 (max range always)", "64 pixels"],
            "25 units away on average",
            "01a cell 20.",
            _src(s01a, 20),
        )
    )
    items.append(
        _q(
            "repeat-interleave",
            "mcq",
            "application",
            3,
            "clip-style",
            "For x=[1,2,3], 02b shows x.repeat(3) vs x.repeat_interleave(3). Which is [1,1,1,2,2,2,3,3,3]?",
            ["repeat_interleave", "repeat", "unflatten", "argmax"],
            "repeat_interleave",
            "repeat tiles the whole vector; repeat_interleave repeats each element.",
            _src(s02b, 33),
        )
    )
    items.append(
        _q(
            "vss-models-endpoint",
            "mcq",
            "recall",
            1,
            "vss",
            "GET /models on VSS tells you…",
            ["The LLM configured at VSS startup (OpenAI-compatible)", "All GPUs on Earth", "Neo4j password", "FashionMNIST classes"],
            "The LLM configured at VSS startup (OpenAI-compatible)",
            "04a 4.2.",
            _src(s04a, 14),
        )
    )
    items.append(
        _q(
            "cypher-wears",
            "code_interp",
            "apply",
            3,
            "g-retriever",
            "What does MATCH p=()-[r:WEARS]->() RETURN p retrieve in 04b?",
            [
                "All graph paths whose relationship type is WEARS",
                "All Milvus vectors",
                "Only the worker node isolated",
                "The MP4 container header",
            ],
            "All graph paths whose relationship type is WEARS",
            "04b 4.4.1 — relationship names may need edits if the extractor used different labels.",
            _src(s04b, 31),
        )
    )
    items.append(
        _q(
            "unet-vs-cnn",
            "compare",
            "compare",
            3,
            "unet",
            "Why does 01b mention U-Net rather than a plain classification CNN for CT?",
            [
                "U-Nets highlight anomalous regions (segmentation) on 3D medical volumes",
                "U-Net is required to open NIfTI files",
                "U-Net replaces Nyquist",
                "U-Net is the VSS VLM",
            ],
            "U-Nets highlight anomalous regions (segmentation) on 3D medical volumes",
            "01b closing CT paragraph.",
            _src("01b_Exploring_Modalities.ipynb", 32),
        )
    )
    items.append(
        _q(
            "hi-res-tables",
            "troubleshooting",
            "diagnose",
            3,
            "table-transformer",
            "partition_pdf returned text but no HTML tables. Which 03b flags are missing?",
            ["infer_table_structure=True and strategy='hi_res'", "chunking_strategy=by_title only", "enable_chat", "Net(8)"],
            "infer_table_structure=True and strategy='hi_res'",
            "03b 3.3.",
            _src(s03b, 20),
        )
    )
    items.append(
        _q(
            "predict-fusion-cubes",
            "prediction",
            "apply",
            4,
            "intermediate-concat",
            "Predict: on colored cubes, which qualitative valid-loss ordering matches the course motivation (not a stored CSV in this clone)?",
            [
                "LiDAR-only worst on valid (overfit); intermediate fusion should beat unimodal RGB by mixing color+geometry",
                "LiDAR-only best on valid because depth is metric",
                "Early fusion illegal on cubes",
                "All four fusion nets must tie",
            ],
            "LiDAR-only worst on valid (overfit); intermediate fusion should beat unimodal RGB by mixing color+geometry",
            "Labeled EXPECTED_RESULT from 02a narrative; run the twin as SIMULATED_RESULT.",
            _src(s02a, 7),
        )
    )
    items.append(
        _q(
            "design-cilp-pipeline",
            "architecture",
            "design",
            5,
            "cilp",
            "Design the 05 pipeline to classify RGB with a LiDAR-trained head. Correct order?",
            [
                "Train CILP on paired RGB↔LiDAR → freeze CILP → train projector to lidar_cnn.get_embs → freeze lidar_cnn → optional projector fine-tune with BCE",
                "Fine-tune lidar_cnn on RGB pixels directly, discard CILP",
                "Use VSS /summarize on PNG files",
                "Concat RGB and LiDAR in Net(8) and call it CILP",
            ],
            "Train CILP on paired RGB↔LiDAR → freeze CILP → train projector to lidar_cnn.get_embs → freeze lidar_cnn → optional projector fine-tune with BCE",
            "Assessment architecture.",
            _src(s05, 29),
        )
    )
    items.append(
        _q(
            "gpu-reset-not-training",
            "mcq",
            "recall",
            1,
            "multimodal-ai",
            "00_jupyterlab kernel shutdown is…",
            ["A way to clear GPU memory between labs, not a training result", "An ACTUAL_RUN of CILP", "Graph-RAG ingest", "Proof MSE decreased"],
            "A way to clear GPU memory between labs, not a training result",
            "00 and end-of-lab IPython shutdown cells.",
            _src("00_jupyterlab.ipynb", 5),
        )
    )
    return items


def _concept_family(concept: dict) -> list[dict]:
    slug = concept["slug"]
    name = concept["name"]
    src = concept["source"]
    file = src.get("file", "")
    out = []
    # Recall definition
    wrong = [
        "A Kubernetes autoscaler (not taught as that in this course)",
        "A Dynamo KV router (not this DLI course)",
        "An ElevenLabs voice id",
    ]
    out.append(
        _q(
            f"rec-{slug}-def",
            "mcq",
            "recall",
            1,
            slug,
            f"Which statement matches how this NVIDIA multimodal course uses **{name}**?",
            [concept["engineer"][:220], *wrong],
            concept["engineer"][:220],
            concept["school"],
            src,
        )
    )
    out.append(
        _q(
            f"rec-{slug}-file",
            "mcq",
            "recall",
            1,
            slug,
            f"Which notebook is the primary source cited for {name}?",
            [file, "Lab_03_03_Disaggregated_vLLM.ipynb", "inferencing ai.pdf", "Grove_PodGang.ipynb"],
            file,
            f"Provenance pointer {src}.",
            src,
        )
    )
    out.append(
        _q(
            f"app-{slug}-eng",
            "short_answer",
            "apply",
            3,
            slug,
            f"In one or two sentences, give an engineer-level reason you would reach for {name} in a system like the labs.",
            [],
            concept["engineer"][:280],
            "Grade by covering the engineer gist; tutor uses rubrics.",
            src,
        )
    )
    out.append(
        _q(
            f"trb-{slug}",
            "troubleshooting",
            "diagnose",
            3,
            slug,
            f"A teammate's explanation of {name} sounds like: '{concept['school'][:80]}… therefore we can ignore the notebook math.' What is wrong?",
            [
                "School-mode intuition is a start, but operational choices must follow the notebook's actual tensors, APIs, or formulas",
                "School mode is forbidden",
                "Math is never in this course",
                "Ignore evidence labels",
            ],
            "School-mode intuition is a start, but operational choices must follow the notebook's actual tensors, APIs, or formulas",
            "Depth switching preserves facts; it does not replace source.",
            src,
        )
    )
    # Compare with a sibling in same cluster
    siblings = [c for c in CONCEPTS if c["cluster"] == concept["cluster"] and c["slug"] != slug]
    if siblings:
        other = siblings[0]
        out.append(
            _q(
                f"cmp-{slug}-{other['slug']}"[:170],
                "compare",
                "compare",
                3,
                slug,
                f"Contrast **{name}** with **{other['name']}** as used in this course.",
                [
                    f"{name}: {concept['engineer'][:110]} vs {other['name']}: {other['engineer'][:110]}",
                    "They are identical course terms",
                    "Both are KEDA replica counts",
                    "Neither appears in the notebooks",
                ],
                f"{name}: {concept['engineer'][:110]} vs {other['name']}: {other['engineer'][:110]}",
                "Keep the missing distinction explicit.",
                src,
            )
        )
    out.append(
        _q(
            f"nb-{slug}-cell",
            "notebook",
            "apply",
            2,
            slug,
            f"You open {file} at cell {src.get('cell_index')}. What evidence class is the markdown/code at that locator?",
            ["COURSE_SOURCE", "ACTUAL_RUN (this clone always stores outputs)", "EXTERNAL_RESEARCH", "SIMULATED_RESULT by default for notebooks"],
            "COURSE_SOURCE",
            "Notebook text/code is course source. Blank outputs are not ACTUAL_RUN.",
            src,
        )
    )
    out.append(
        _q(
            f"arch-{slug}",
            "architecture",
            "design",
            4,
            slug,
            f"Where does {name} sit in a production-shaped pipeline inspired by the labs (still source-grounded)?",
            [
                f"Use it where the course places it: {concept['cluster']} — {concept['engineer'][:140]}",
                "Always as the Envoy AI Gateway",
                "Always as Grove PodGang",
                "Delete it if using RGB",
            ],
            f"Use it where the course places it: {concept['cluster']} — {concept['engineer'][:140]}",
            "Do not import inference-serving architecture from a different NVIDIA course.",
            src,
        )
    )
    if concept.get("misconceptions"):
        mslug = concept["misconceptions"][0]
        m = next((x for x in MISCONCEPTIONS if x["slug"] == mslug), None)
        if m:
            out.append(
                _q(
                    f"mis-{slug}-{mslug}"[:170],
                    "mcq",
                    "diagnose",
                    3,
                    slug,
                    f"Which belief about {name} is the documented misconception?",
                    [m["confused"], "Citations must include cell indexes", "Evidence labels should be visible", "Notebooks must not auto-exec kubectl"],
                    m["confused"],
                    m["simple_correction"],
                    m["source"],
                    mslug,
                )
            )
    return out


def _code_fill_fixmes() -> list[dict]:
    s01a = "01a_Early_and_Late_Fusion.ipynb"
    s02b = "02b_Contrastive_Pretraining.ipynb"
    items = []
    items.append(
        _q(
            "fixme-outline-threshold",
            "fill_fixme",
            "apply",
            3,
            "sobel-outline",
            "02b outline_img: pixels above which threshold become 1 before Sobel?",
            ["0.25", "0.5", "50.0", "255"],
            "0.25",
            "threshold = 0.25 in the solution cell.",
            _src(s02b, 20),
        )
    )
    items.append(
        _q(
            "fixme-outline-conv",
            "fill_fixme",
            "apply",
            3,
            "sobel-outline",
            "Which PyTorch op applies Gx and Gy in the outline_img solution?",
            ["F.conv2d", "F.linear", "F.max_pool2d", "F.embedding"],
            "F.conv2d",
            "02b solution cell.",
            _src(s02b, 20),
        )
    )
    items.append(
        _q(
            "net-positions",
            "notebook",
            "recall",
            2,
            "cnn-position",
            "num_positions in 01a Net is 9 because…",
            ["3 objects × xyz", "3 RGB channels × 3", "9 LiDAR beams", "batch size 9"],
            "3 objects × xyz",
            "01a dataset discussion.",
            _src(s01a, 46),
        )
    )
    items.append(
        _q(
            "img-size-01a",
            "notebook",
            "recall",
            1,
            "rgb-camera",
            "IMG_SIZE used for the fusion labs is…",
            ["64", "224", "28", "512"],
            "64",
            "01a PyTorch data section. 03a flowers use 224 for VGG.",
            _src(s01a, 42),
        )
    )
    items.append(
        _q(
            "fashion-28",
            "notebook",
            "recall",
            1,
            "clip-style",
            "FashionMNIST contrastive embedder img_size in 02b is…",
            ["28", "64", "224", "1024"],
            "28",
            "ContrastivePretraining(1, 28).",
            _src(s02b, 40),
        )
    )
    return items


def _sequence_and_design() -> list[dict]:
    items = []
    items.append(
        _q(
            "seq-vss-pipeline",
            "sequence",
            "design",
            4,
            "ca-rag",
            "Order the VSS summarization pipeline stages from 04a.",
            [
                "Split video into chunks",
                "VLM captions per chunk (prompt)",
                "LLM caption summarization over a batch",
                "LLM summary aggregation",
            ],
            "Split video into chunks|VLM captions per chunk (prompt)|LLM caption summarization over a batch|LLM summary aggregation",
            "Milvus ingest of captions happens in parallel.",
            _src("04a_VSS.ipynb", 33),
        )
    )
    items.append(
        _q(
            "seq-ocr",
            "sequence",
            "design",
            4,
            "ocr",
            "Order a 03b-style multimodal PDF pipeline.",
            [
                "partition_pdf / OCR",
                "chunk (ideally by_title)",
                "table + figure extraction",
                "embed for RAG",
            ],
            "partition_pdf / OCR|chunk (ideally by_title)|table + figure extraction|embed for RAG",
            "NV-YOLOX can locate layout boxes on rasterized pages.",
            _src("03b_OCR_Pipelines.ipynb", 1),
        )
    )
    items.append(
        _q(
            "seq-lidar-vis",
            "sequence",
            "apply",
            3,
            "lidar-xyza",
            "Order the 01a steps to visualize a point cloud from a depth grid.",
            [
                "Load depth, azimuth, zenith",
                "Compute x,y,z surfaces and max-range mask a",
                "Scatter only where a==1",
                "Optionally animate view_init",
            ],
            "Load depth, azimuth, zenith|Compute x,y,z surfaces and max-range mask a|Scatter only where a==1|Optionally animate view_init",
            "01a 1.1.3.",
            _src("01a_Early_and_Late_Fusion.ipynb", 30),
        )
    )
    # Extra assessment-level scenarios
    for i, (title, concept, prompt, ans, exp, file, cell) in enumerate(
        [
            (
                "fusion-choice-defense",
                "intermediate-concat",
                "A PM wants late fusion because 'ensembles always win' on colored cubes. Your defense?",
                "Late fusion joins heads after each net already collapsed space — color×geometry interactions may need intermediate concat/matmul",
                "02a motivation.",
                "02a_Intermediate_Fusion.ipynb",
                24,
            ),
            (
                "vss-its-defense",
                "vlm-prompt-persona",
                "Generic caption 'Write a caption based on the video clip' produced a useless ITS report. Defend your next change.",
                "Rewrite VLM persona/details/format to demand timestamped traffic events; keep aggregation from inventing unseen facts",
                "04a 4.3 vs 4.5.",
                "04a_VSS.ipynb",
                48,
            ),
            (
                "graph-ppe-defense",
                "graph-rag",
                "Vector-RAG says it cannot answer 'who wore PPE while carrying the box'. Defend Graph-RAG.",
                "Need WEARS and CARRIES relations; Graph-RAG stores those edges after enable_chat ingest",
                "04b warehouse Q&A.",
                "04b_VSS_GraphRAG.ipynb",
                16,
            ),
        ]
    ):
        items.append(
            _q(
                f"defend-{title}",
                "free_response",
                "defend",
                6,
                concept,
                prompt,
                [],
                ans,
                exp,
                _src(file, cell),
            )
        )
    return items
