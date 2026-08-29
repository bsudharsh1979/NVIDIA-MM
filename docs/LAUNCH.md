# Launch runbook — Modality Twin Academy

Not affiliated with or endorsed by NVIDIA. `course-materials/` is bring-your-own personal-use content.

## Local (zero keys)

```bash
pip install -r services/api/requirements.txt
./scripts/dev-api.sh
# other terminal
cd apps/web && npm install && npm run dev
```

Open http://127.0.0.1:3000

## Tests

```bash
pytest tests/backend -q
cd apps/web && npx next lint && npm run build
```

## Live URLs (profile `gamgn`)

- API: https://gamgn--modality-twin-academy-api-fastapi-app.modal.run
- Web: https://gamgn--modality-twin-academy-web-web.modal.run
- Modal apps: https://modal.com/apps/gamgn/main/deployed/modality-twin-academy-api and https://modal.com/apps/gamgn/main/deployed/modality-twin-academy-web

`MODAL_MIN_CONTAINERS=0`. Provider keys live in the Modal secret `academy-env` (not the git repo).

## Modal

Profile `gamgn`. Keep `MODAL_MIN_CONTAINERS=0` unless you want an always-warm demo container.

Keep `MODAL_MIN_CONTAINERS=0` if you want cold-start savings on the $30/month plan. Use `1` only when you need an always-warm container for a live demo.

Create an empty-capable secret once:

```bash
modal secret create academy-env DEMO_MODE=1
```

Deploy sequence:

```bash
MODAL_MIN_CONTAINERS=0 MODAL_MAX_CONTAINERS=1 modal deploy deploy/modal/modal_app.py
# copy the printed https://*.modal.run URL
NEXT_PUBLIC_API_BASE=<api URL from step 1> MODAL_MIN_CONTAINERS=0 MODAL_MAX_CONTAINERS=1 \
  modal deploy deploy/modal/modal_web.py
```

SQLite stays consistent because the API is pinned to `max_containers=1` and `@modal.concurrent(max_inputs=100)`.

## Live verify

Replace `$API` and `$WEB` with the two Modal URLs.

```bash
curl -sS "$API/api/notebooks" | python -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'], d[0]['slug'])"
ID=$(curl -sS "$API/api/notebooks" | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
curl -sS -o /tmp/n1.json -w "%{http_code}\n" "$API/api/notebooks/$ID"
curl -sS -o /tmp/n2.json -w "%{http_code}\n" "$API/api/notebooks/$ID"
python -c "import json; a=json.load(open('/tmp/n1.json')); b=json.load(open('/tmp/n2.json')); assert a['id']==b['id']"
curl -sS -o /dev/null -w "%{http_code}\n" "$API/api/notebooks/01a_Early_and_Late_Fusion.ipynb"
curl -sS -o /dev/null -w "%{http_code}\n" "$API/api/notebooks/01a_Early_and_Late_Fusion/walkthrough"
curl -sS -o /dev/null -w "%{http_code}\n" "$API/api/notebooks/01a_Early_and_Late_Fusion/walkthrough?depth=expert"
curl -sS -o /dev/null -w "%{http_code}\n" "$API/api/voice/status"
curl -sS -o /dev/null -w "%{http_code}\n" "$WEB/notebooks"
```

Ids must match across the two detail fetches (deterministic `sha1(path)`, not uuid4).

## First five clicks

1. Home → take the diagnostic (or skip to Notebooks).
2. Open `02a_Intermediate_Fusion` → **Play audio lecture** (SIMPLE default) → next/prev/jump → toggle EXPERT.
3. Digital Twins → Fusion lab → write a prediction → run the colored-cubes / LiDAR scenario.
4. Risks → open any drill (incident diagnosis withholds truth until you commit).
5. Tutor (Demo) → ask why late fusion loses on colored cubes → check citations.

## Apps

- API app name: `modality-twin-academy-api`
- Web app name: `modality-twin-academy-web`
