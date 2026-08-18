#!/usr/bin/env python3
"""Promote the exact browser-validated Zircon desktop control floor.

Browser QA run 32175607481 validated the exact build artifact for ORIGINS SHA
40d5140805bede9f1c7c5af8c2fb0cefc284856c in Chrome across all 80 windows.
That artifact contained 2674 GameScene + 149 nested controls with zero browser
failures/errors and a passing Chat Options Add/Remove smoke.

Future source growth is allowed, but it immediately becomes pending again until
a later exact-SHA Browser QA promotion updates the validated constants/evidence.
"""
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
    windows = spec.get("windows", [])
    nested = spec.get("nestedWindows", [])
    game = sum(len(window.get("controls", [])) for window in windows)
    nested_count = sum(len(window.get("controls", [])) for window in nested)
    final = spec.get("finalSupplementalSourceMatrix") or {}
    failures: list[str] = []

    if len(windows) != 65:
        failures.append(f"GameScene windows {len(windows)} != 65")
    if len(nested) != 15:
        failures.append(f"nested windows {len(nested)} != 15")
    if game < VALIDATED_GAME:
        failures.append(f"GameScene controls {game} < browser-validated {VALIDATED_GAME}")
    if nested_count < VALIDATED_NESTED:
        failures.append(f"nested controls {nested_count} < browser-validated {VALIDATED_NESTED}")
    if final.get("passed") is not True:
        failures.append(f"prior final matrix missing/not PASS: {final}")

    pending = game != VALIDATED_GAME or nested_count != VALIDATED_NESTED

    final.update({
        "gameSceneControls": game,
        "nestedControls": nested_count,
        "minimumGameSceneControls": VALIDATED_GAME,
        "minimumNestedControls": VALIDATED_NESTED,
        "latestSourceAuditedGameSceneFloor": game,
        "latestSourceAuditedNestedFloor": nested_count,
        "browserValidatedGameSceneFloor": VALIDATED_GAME,
        "browserValidatedNestedFloor": VALIDATED_NESTED,
        "browserValidatedFloorPending": pending,
        "browserValidationEvidenceSha": EVIDENCE_SHA,
        "browserValidationEvidenceRun": EVIDENCE_RUN,
        "browserValidationEvidenceWindows": 80,
        "browserValidationEvidenceFailures": 0,
        "browserValidationEvidenceErrors": 0,
        "passed": final.get("passed") is True and not failures,
        "failures": list(final.get("failures") or []) + failures,
    })
    spec["finalSupplementalSourceMatrix"] = final
    spec["currentSourceControlFloor"] = {
        "passed": not failures,
        "gameScene": game,
        "nested": nested_count,
        "windows": [65, 15],
        "browserValidatedGameScene": VALIDATED_GAME,
        "browserValidatedNested": VALIDATED_NESTED,
        "browserValidationPending": pending,
        "browserValidationEvidenceSha": EVIDENCE_SHA,
        "browserValidationEvidenceRun": EVIDENCE_RUN,
        "runtimePayloadsInvented": False,
        "controlsFabricatedByAudit": False,
    }

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Current source/browser floor failed:\n- " + "\n- ".join(failures))

    state = "pending newer source growth" if pending else "browser-validated"
    print(f"Current source floor: PASS -> {game}+{nested_count}; {state}; evidence run {EVIDENCE_RUN}")


if __name__ == "__main__":
    main()
