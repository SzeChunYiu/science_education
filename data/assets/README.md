# Shared Asset Library

This folder is for reusable generated assets that can be shared across subjects or reused across multiple production runs.

Rules:

- reusable subject asset libraries live here
- one-off rendered episode media stays under `output/`
- test packs for asset generation also live here if they are part of the reusable library evaluation process

Current layout:

- `physics/` — reusable physics asset library

Generation helpers:

- `python3 -m src.generate_physics_assets --manifest data/assets/physics/manifests/phase1_core_assets.json`
