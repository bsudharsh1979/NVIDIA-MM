# Implementation plan — Modality Twin Academy

Adapted from the Inference Twin Academy master spec to **this** course (multimodal fusion, contrastive pre-training, OCR, VSS, Graph-RAG), not inference serving (NIM/KEDA/Dynamo).

## Product principles (unchanged)

1. Source-grounded to `/course-materials`
2. Evidence integrity (never label a twin as `ACTUAL_RUN`)
3. Active learning (predict → experiment → explain)
4. Visual systems learning (fusion graphs, VSS pipeline, LiDAR beams)
5. Learn from the tutor’s own inference telemetry when a real provider is used

## Phase map

| Phase | Status |
| --- | --- |
| Inspect notebooks + missing Omniverse repo | Done |
| Foundation: ingest, provenance, SQLite/Postgres, hybrid search, concept graph | Build |
| Learning engine: diagnostic, mastery, FSRS, questions, misconceptions | Build |
| Tutor: Demo / OpenAI / NIM / Hugging Face + Course vs Research | Build |
| Notebook Studio for all 10 notebooks | Build |
| Digital twins (web) + TwinStateEngine | Build |
| Experiment importer + comparison workbench | Build |
| Voice adapters (optional) | Build |
| Omniverse bridge stub | Build |
| Docker Compose local demo (no API keys) | Build |
| Tests + docs | Build |

## Digital twins for *this* course

1. **LiDAR geometry** — azimuth/zenith → XYZ (course math)
2. **Fusion lab** — early / late / concat / matmul vs RGB-only / LiDAR-only
3. **Modality explorer** — spectrogram, CT slice, RGB, LiDAR
4. **Contrastive space** — cosine matrix, Sobel outlines
5. **Projection lab** — frozen encoder + projector
6. **OCR pipeline** — partition → chunk → table/image → NV-YOLOX boxes
7. **VSS CA-RAG** — chunking, VLM captions, LLM aggregate, Milvus
8. **Graph-RAG** — extract / retrieve / generate
9. **CILP assessment arena** — worker-ratio analog is **architecture defense** (CILP + projector)

## Provider defaults

The UI **asks which API to use**. Offline **Demo** is the default so `docker compose up` works with zero keys.

| Slot | Options |
| --- | --- |
| Tutor | Demo, OpenAI, NVIDIA NIM, Hugging Face Inference |
| Voice | Off, ElevenLabs, Sarvam, OpenAI Realtime |
| Research | Off, Perplexity |

Never silently switch providers.

## Non-goals for this pass

- Enterprise SSO / billing
- Executing notebook `kubectl` / training loops
- Rebuilding a full Omniverse Kit application
