# ORIGINS overrides on pinned Zircon

ORIGINS keeps `Suprcode/Zircon` pinned to a known upstream commit and applies only small, explicit source replacements from this directory after checkout.

The relative path under `overrides/zircon/` must match the path in the pinned Zircon tree. `scripts/bootstrap-zircon.sh` and `.ps1` copy these files into `vendor/zircon` after verifying the upstream commit.

Rules:

- Never fork a second server/combat engine.
- Keep an override only when ORIGINS behavior differs intentionally from pinned Zircon.
- Each magic override must have a behavior decision under `database/magic/`.
- Crystal database/persistence code is never copied here.
- Crystal-derived behavior is ported only inside Zircon primitives (`MagicObject`, `Player.MagicAttack`, delayed actions, buffs, `SpellObject`).
- CI compiles the overridden source against the exact pinned Zircon revision.
