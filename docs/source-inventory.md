# Source inventory — NVIDIA Multimodal course

**Product:** Modality Twin Academy  
**Course:** NVIDIA DLI — Building Multimodal AI Applications  
**Repository at inspection:** `github.com/bsudharsh1979/NVIDIA-MM`  
**Inspected:** 2026-08-25

## What is in this repository

The clone contained **ten Jupyter notebooks** and **no** PDF/PPTX decks, images, datasets, `utils.py`, assessment weights, or Omniverse Kit application. Filenames were discovered automatically; the ingestion engine does not hard-require these names.

| File | Cells | Role |
| --- | --- | --- |
| `00_jupyterlab.ipynb` | 8 | JupyterLab orientation; GPU memory reset |
| `01a_Early_and_Late_Fusion.ipynb` | 72 | Omniverse synthetic RGB + LiDAR; XYZ from azimuth/zenith; single-modal CNN; late fusion; early fusion |
| `01b_Exploring_Modalities.ipynb` | 37 | Audio WAV → spectrogram; CT NIfTI; U-Net mention |
| `02a_Intermediate_Fusion.ipynb` | 37 | Colored cubes dataset; EarlyNet, LateNet, ConcatIntermediateNet, MatmulIntermediateNet |
| `02b_Contrastive_Pretraining.ipynb` | 64 | FashionMNIST outlines (Sobel); cosine similarity; CLIP-style contrastive model; vector lookup |
| `03a_Projection.ipynb` | 67 | Cross-modal projection (text → image space); VGG16 flower classifier; CLIP text encoder |
| `03b_OCR_Pipelines.ipynb` | 89 | Unstructured PDF partition; table-transformer; YOLOX; NV-YOLOX page elements; GB200 NVL72 datasheet |
| `04a_VSS.ipynb` | 85 | NVIDIA VSS blueprint; `/files`, `/summarize`; CA-RAG; Milvus; chunk duration; prompts |
| `04b_VSS_GraphRAG.ipynb` | 40 | Vector-RAG vs Graph-RAG; `/chat/completions`; G-Extraction / G-Retriever / G-Generation; Neo4j |
| `05_Assessment.ipynb` | 52 | CILP (Contrastive Image LiDAR Pre-training) + projector onto frozen LiDAR CNN |

**Missing from this clone (referenced by notebooks, not shipped):**

- `images/` (DLI headers, LiDAR diagrams, VSS architecture, etc.)
- `data/` (Omniverse replicator RGB/LiDAR, cubes dataset, FashionMNIST cache, flower photos, PDFs, videos)
- `utils.py`, `assessment/assesment_utils.py`, `assessment/lidar_cnn.pt`, `run_assessment.py`
- Slide decks mentioned as “next slide deck” after 01a
- Any Omniverse Kit / OpenUSD digital-twin repository

## Course progression (as taught)

```text
JupyterLab
  → Early/late fusion (RGB + LiDAR, Omniverse SDG)
  → Other modalities (audio, CT)
  → Intermediate fusion (concat vs matmul) on color-critical cubes
  → Contrastive pre-training (CLIP pattern, not only language-image)
  → Cross-modal projection (reuse a frozen unimodal model)
  → OCR / document RAG (unstructured + NV-YOLOX)
  → VSS summarization + CA-RAG (VILA NIM, Milvus)
  → VSS Graph-RAG (Neo4j, Cypher)
  → Assessment: CILP + RGB→LiDAR classifier
```

## Evidence status of notebook experiments

Notebooks contain **code and expected training behavior**. This clone does **not** include stored cell outputs or CSV training curves except where notebooks *load* CSVs that are not present.

| Claim | Evidence class |
| --- | --- |
| Architecture definitions, API shapes, formulas in markdown/code | `COURSE_SOURCE` |
| “Loss should be under 3.2”, “accuracy above .70 / .95” | `EXPECTED_RESULT` (assessment criteria; not proven here) |
| Colored-cube RGB valid loss ≈ 6; LiDAR train < 1 and valid > 8 | `EXPECTED_RESULT` (notebook narrative; CSV not in clone) |
| Twin charts in this academy | `SIMULATED_RESULT` |
| Imported AIPerf / kubectl / JSON | `ACTUAL_RUN` |

## Ingestion targets

All ten notebooks are ingested as `SourceArtifact` + per-cell `SourceSpan` / `NotebookCell`. PDF/PPTX parsers are implemented and will pick up files added later under `/course-materials`.
