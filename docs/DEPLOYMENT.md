# Deployment

**Local:** `docker compose up --build` → web `:3000`, api `:8000`.

**Vercel:** deploy `apps/web`; set rewrite to the API (`deploy/vercel/vercel.json`).

**Modal:** `deploy/modal/app.py` — optional burst; Docker remains first-class.

**NVIDIA:** see `deploy/nvidia/README.md`.
