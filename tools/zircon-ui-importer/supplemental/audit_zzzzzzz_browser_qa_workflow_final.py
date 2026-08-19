#!/usr/bin/env python3
"""Final bridge for promoted exact-SHA Browser QA guarantees."""
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
    final = spec.get("finalSupplementalSourceMatrix") or {}
    qa = spec.get("browserQaWorkflowAudit") or {}
    failures: list[str] = []

    if final.get("passed") is not True:
        failures.append(f"prior final matrix missing/not PASS: {final}")
    expected = {
        "passed": True,
        "exactShaBuildArtifactRequired": True,
        "artifactName": "zircon-ui-reference-complete",
        "expectedWindows": 80,
        "browserValidatedGameFloor": 2674,
        "browserValidatedNestedFloor": 149,
        "promotionEvidenceSha": "40d5140805bede9f1c7c5af8c2fb0cefc284856c",
        "promotionEvidenceRun": 32175607481,
        "supportsFutureSourceGrowthAsPending": True,
        "chatOptionsSmokeRequired": True,
        "failureEvidenceUploaded": True,
        "runtimePayloadsInvented": False,
    }
    for key, value in expected.items():
        if qa.get(key) != value:
            failures.append(f"Browser QA workflow contract drifted: {key}={qa.get(key)!r}, expected {value!r}")

    final.update({
        "browserQaWorkflowPassed": qa.get("passed") is True,
        "browserQaExactShaArtifact": qa.get("exactShaBuildArtifactRequired") is True,
        "browserQaExpectedWindows": qa.get("expectedWindows"),
        "browserQaValidatedGameFloor": qa.get("browserValidatedGameFloor"),
        "browserQaValidatedNestedFloor": qa.get("browserValidatedNestedFloor"),
        "browserQaPromotionEvidenceSha": qa.get("promotionEvidenceSha"),
        "browserQaPromotionEvidenceRun": qa.get("promotionEvidenceRun"),
        "passed": final.get("passed") is True and not failures,
        "failures": list(final.get("failures") or []) + failures,
    })
    spec["finalSupplementalSourceMatrix"] = final
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Final Browser QA workflow contract failed:\n- " + "\n- ".join(failures))
    print("Final Browser QA workflow: PASS -> browser-validated floor 2674+149, exact-SHA evidence locked")


if __name__ == "__main__":
    main()
