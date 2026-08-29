# NVIDIA Omniverse deployment

Keep streaming / NVCF **separate** from `docker compose up`.

1. Run the academy API + web as usual.
2. `docker compose --profile omniverse up omniverse-bridge`
3. Point a Kit extension at `ws://localhost:8010/twin`.
4. NVCF: package the Kit app independently; pass `OMNIVERSE_BRIDGE_URL` to reach the academy state service.

The learning UI must never block on this path.
