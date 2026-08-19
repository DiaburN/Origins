#!/usr/bin/env python3
"""Strict contract for the exact-artifact Browser QA workflow after promotion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

VALIDATED_GAME = 2674
VALIDATED_NESTED = 149
EVIDENCE_SHA = "40d5140805bede9f1c7c5af8c2fb0cefc284856c"
EVIDENCE_RUN = 32175607481


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[3]
    path = root / ".github/workflows/browser-qa-zircon-ui-reference.yml"
    if not path.exists():
        raise SystemExit("Browser QA workflow missing")
    text = path.read_text(encoding="utf-8")

    required = (
        "name: Browser QA Zircon UI reference",
        "build-zircon-ui-reference.yml/runs?head_sha=${GITHUB_SHA}",
        "zircon-ui-reference-complete",
        "browser-qa-runtime.js",
        "browser-qa-window-runtime.js",
        "browser-qa-chat-options-runtime.js",
        "browser-qa-result",
        "report.get('testedWindows') != 80",
        "browserValidatedGameScene",
        "browserValidatedNested",
        "browserValidationPending",
        EVIDENCE_SHA,
        str(EVIDENCE_RUN),
        "2674",
        "149",
        ".qa/chat-options-browser-qa-report.json",
        "zircon-ui-browser-qa-${{ github.sha }}",
        "if: always()",
    )
    for needle in required:
        if needle not in text:
            raise SystemExit(f"Browser QA workflow contract drifted: {needle}")

    forbidden = (
        "floor.get('gameScene') != 2511",
        "floor.get('browserValidationPending') is not True",
        "final.get('minimumGameSceneControls') != 2507",
        "latestSourceAuditedGameSceneFloor') != 2511",
        "2511 checkpoint eligible for promotion",
    )
    for needle in forbidden:
        if needle in text:
            raise SystemExit(f"Browser QA contains obsolete pre-promotion contract: {needle}")

    spec["browserQaWorkflowAudit"] = {
        "passed": True,
        "exactShaBuildArtifactRequired": True,
        "artifactName": "zircon-ui-reference-complete",
        "expectedWindows": 80,
        "browserValidatedGameFloor": VALIDATED_GAME,
        "browserValidatedNestedFloor": VALIDATED_NESTED,
        "promotionEvidenceSha": EVIDENCE_SHA,
        "promotionEvidenceRun": EVIDENCE_RUN,
        "supportsFutureSourceGrowthAsPending": True,
        "chatOptionsSmokeRequired": True,
        "failureEvidenceUploaded": True,
        "runtimePayloadsInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Browser QA workflow audit: PASS -> exact SHA, 80 windows, validated floor 2674+149")


if __name__ == "__main__":
    main()
