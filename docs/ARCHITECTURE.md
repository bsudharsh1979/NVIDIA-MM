# Architecture

## Packages

| Path | Responsibility |
| --- | --- |
| `apps/web` | Next.js App Router UI |
| `services/api` | FastAPI domains: course, retrieval, tutor, mastery, questions, review, experiments, twins, providers, voice, research |
| `services/twin-engine` | Canonical `TwinState` JSON |
| `services/omniverse-bridge` | Optional WebSocket → OpenUSD-oriented prims |
| `course-materials` | NVIDIA DLI notebooks (source of truth) |
| `integrations/omniverse-twin` | Kit drop-in (not shipped in the original clone) |

## Data

SQLite by default (`DATABASE_URL`). PostgreSQL + pgvector is a swap of the URL; embeddings today are cached hashed vectors so the app runs offline. OpenAI/NIM embeddings can replace the hash provider without changing the span table.

## Tutor providers

`TutorModelProvider` with Demo, OpenAI, NVIDIA NIM, Hugging Face. The rest of the code never imports `openai` directly.

## Security

Uploaded experiments and notebook cells are **data**. No `eval`, no `kubectl` from notebooks, no SSRF fetch of learner-supplied URLs in ingest. Markdown in the UI is rendered as text/pre, not raw HTML from course files.
