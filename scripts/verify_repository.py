#!/usr/bin/env python3
"""Fast structural verification for the ORIGINS integration branch."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ".cursor/rules/00-project-safety.mdc",
    ".cursor/rules/10-game-architecture.mdc",
    ".cursor/rules/20-origins-runtime-decisions.mdc",
    "docs/MASTER_PROJECT_STATE.md",
    "docs/CURSOR_IMPLEMENTATION_PLAN.md",
    "origins/map-engine/themes/zuma/theme.json",
    "origins/map-engine/themes/zuma/rooms/standard-long-01.json",
    "origins/map-engine/themes/zuma/rooms/king-room-01.json",
    "packages/game-core/src/character-movement/CharacterMovementController.ts",
    "packages/game-core/src/character-movement/crystal-animation-profile.ts",
    "tools/crystal-character-importer/extract_player_locomotion.py",
    "tools/crystal-map-importer/extract_theme_assets_complete.py",
    "tools/zircon-ui-importer/extract_zl_assets.py",
    "apps/zircon-ui-reference/index.html",
    "apps/game-web/README.md",
]

missing = [path for path in REQUIRED if not (ROOT / path).exists()]
if missing:
    print("ORIGINS repository verification FAILED")
    for path in missing:
        print("MISSING:", path)
    sys.exit(1)

print("ORIGINS repository verification OK")
print(f"Checked {len(REQUIRED)} integration anchors.")
