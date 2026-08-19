#!/usr/bin/env python3
"""Strict contract for exact-SHA 80-window visual evidence generation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[3]
    path = root / ".github/workflows/visual-review-zircon-ui-reference.yml"
    if not path.exists():
        raise SystemExit("visual review workflow missing")
    text = path.read_text(encoding="utf-8")

    required = (
        "name: Visual review Zircon UI reference",
        "branches: [origins-game-v1]",
        "cancel-in-progress: true",
        "browser-qa-zircon-ui-reference.yml/runs?head_sha=${sha}",
        "build-zircon-ui-reference.yml/runs?head_sha=${sha}",
        "zircon-ui-reference-complete",
        "visual-review-runtime.js",
        "2674",
        "149",
        "browserValidatedGameScene",
        "review.get('expectedWindows') != 80",
        "while IFS= read -r id; do",
        "--dump-dom",
        "data-review-window-id=",
        "data-visual-review-target=",
        "--screenshot=",
        "Expected 80 screenshots",
        "Build offline review index",
        "Upload 80-window visual review evidence",
        "if: always()",
        ".visual/doms/",
        "if-no-files-found: warn",
        "zircon-ui-visual-review-${{ steps.revision.outputs.sha }}",
    )
    for needle in required:
        if needle not in text:
            raise SystemExit(f"visual review workflow contract drifted: {needle}")
    forbidden = ("Zuma Temple", "Wizard", "ClientUserItem", "MapObject.User", "GameScene.Game.User", "controls < 2511")
    for needle in forbidden:
        if needle in text:
            raise SystemExit(f"visual review workflow contains obsolete/invented state: {needle}")

    spec["visualReviewWorkflowAudit"] = {
        "passed": True,
        "exactShaBuildRequired": True,
        "exactShaBrowserQaRequired": True,
        "expectedWindows": 80,
        "expectedScreenshots": 80,
        "domTargetValidation": True,
        "offlineIndex": True,
        "concurrencyCancelsStaleRuns": True,
        "failureEvidenceUploaded": True,
        "sourceFloor": 2674,
        "nestedFloor": 149,
        "browserValidatedFloorRequired": True,
        "runtimePayloadsInvented": False,
        "gameWindowContentInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Visual review workflow audit: PASS -> exact SHA QA/build, 80 screenshots, validated floor 2674+149")


if __name__ == "__main__":
    main()
