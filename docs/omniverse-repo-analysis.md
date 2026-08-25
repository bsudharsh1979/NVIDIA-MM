# Omniverse repository analysis

## Finding

This workspace **does not contain** an existing NVIDIA Omniverse / Kit / OpenUSD digital-twin application. Recursive inspection of `NVIDIA-MM` at clone time found only DLI Jupyter notebooks.

The course **uses Omniverse conceptually**:

- NVIDIA Omniverse + Replicator for **synthetic data generation** of RGB, distance, and LiDAR from digital twins of cubes / spheres / tori.
- Assessment CILP trains on Omniverse-generated RGB–LiDAR pairs so a LiDAR classifier can be reused on RGB via contrastive pre-training + projection.

That is **data-generation Omniverse**, not a shipped Kit extension with streaming viewports.

## Integration strategy (do not rebuild a Kit app from scratch)

```text
Web Application
      │
      │ WebSocket / REST
      ▼
Twin State Engine  (canonical JSON, evidence_type=SIMULATED_RESULT)
      │
      ├──── Web 2D/3D twins (this repo — daily learning)
      │
      └──── Omniverse Bridge  (services/omniverse-bridge)
                    │
                    ▼
             Optional Kit app / NVCF streaming
                    │
                  OpenUSD
```

### What we ship now

| Path | Role |
| --- | --- |
| `services/twin-engine` | Canonical simulation state. Web and Omniverse **must not** fork this logic. |
| `services/omniverse-bridge` | WebSocket server that mirrors `TwinState` as OpenUSD-oriented JSON (`prims`, `request_packets`, `kv_blocks` analog for fusion/VSS). |
| `integrations/omniverse-twin` | Drop-in location for a future Kit extension. Contains USD visual-language spec and a stub extension manifest. |
| `deploy/nvidia` | NVCF / streaming notes. **Not** required to run the academy. |

### If you later paste a Kit repo here

1. Place it at `integrations/omniverse-twin/` (do not flatten it into `apps/web`).
2. Keep Kit extensions, USD stages, and streaming code.
3. Subscribe the extension to `OMNIVERSE_BRIDGE_URL` (`ws://…/twin`).
4. Map `TwinState.scenario` → stage variants: `fusion-lab`, `lidar-geometry`, `vss-pipeline`, `graph-rag`, `cilp`.

### Visual language (every prim must teach)

| Prim | Teaches |
| --- | --- |
| RGB camera frustum | Appearance-only sensing; fails in low light (course 01a) |
| LiDAR beam fan | Azimuth/zenith; max-range returns |
| Fusion join node | Early vs late vs intermediate concat/matmul |
| Contrastive similarity matrix | Diagonal = matched pairs |
| VSS chunk bars | `chunk_duration` vs processed frames |
| Graph nodes/edges | G-Extraction entities for warehouse Q&A |
| NIXL analog | Not in this course — do **not** invent disaggregated inference visuals as course fact |

Core learning **must run without** Omniverse, GPU, or NVCF.
