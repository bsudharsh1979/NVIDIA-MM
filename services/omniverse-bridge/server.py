"""Mirrors TwinStateEngine JSON to Omniverse/OpenUSD-oriented prims. Optional."""

from __future__ import annotations

import json
import os

import httpx
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Modality Twin Omniverse Bridge")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
API = os.environ.get("ACADEMY_API", "http://127.0.0.1:8000")


@app.get("/health")
def health():
    return {"ok": True, "omniverse_required": False}


def to_prims(state: dict) -> dict:
    """Visual language — every prim teaches a course idea."""
    scenario = state.get("scenario")
    prims = []
    if scenario == "fusion-lab":
        prims = [
            {"path": "/World/RGBCamera", "teaches": "appearance-only sensing"},
            {"path": "/World/LidarFan", "teaches": "range, not color"},
            {"path": "/World/FusionJoin", "teaches": state.get("controls", {}).get("architecture")},
        ]
    elif scenario == "vss-pipeline":
        prims = [{"path": f"/World/Chunk_{i}", "teaches": "VLM temporal window"} for i in range(int(state.get("metrics", {}).get("chunks") or 1))]
    elif scenario == "graph-rag":
        prims = [{"path": "/World/Worker", "teaches": "entity"}, {"path": "/World/WEARS", "teaches": "relation"}]
    else:
        prims = [{"path": "/World/State", "teaches": scenario}]
    return {"prims": prims, "evidence_type": "SIMULATED_RESULT", "state": state}


@app.websocket("/twin")
async def twin_socket(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_json()
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{API}/api/twins/{msg.get('scenario', 'fusion-lab')}/run", json={"controls": msg.get("controls") or {}, "prediction": msg.get("prediction") or "bridge"})
            await ws.send_json(to_prims(r.json().get("state") or {}))
    except Exception:
        await ws.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
