# Digital twins

`services/twin-engine` is the only simulation logic.

| Twin | Teaches |
| --- | --- |
| lidar-geometry | 01a XYZA |
| fusion-lab | 01a/02a architectures; colored-cube overfit |
| modality-explorer | 01b spectrogram / CT |
| contrastive-space | 02b cosine matrix |
| projection-lab | 03a/05 projector |
| ocr-pipeline | 03b |
| vss-pipeline | 04a chunk math |
| graph-rag | 04b |
| cilp-assessment | 05 gates |

Boundary tests live in `tests/backend/test_twins.py` (no NaN, no negative latency, max-range mask).
