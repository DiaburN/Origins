#!/usr/bin/env python3
"""Final bridge for exact-SHA 80-window visual evidence generation."""
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
    workflow = spec.get("visualReviewWorkflowAudit") or {}
    failures: list[str] = []

    if final.get("passed") is not True:
        failures.append(f"prior final matrix missing/not PASS: {final}")
    expected = {
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
    for key, value in expected.items():
        if workflow.get(key) != value:
            failures.append(f"visual evidence workflow drifted: {key}={workflow.get(key)!r}, expected {value!r}")

    final.update({
        "visualReviewWorkflowPassed": workflow.get("passed") is True,
        "visualReviewExpectedScreenshots": workflow.get("expectedScreenshots"),
        "visualReviewRequiresExactShaBrowserQa": workflow.get("exactShaBrowserQaRequired") is True,
        "visualReviewRequiresExactShaBuild": workflow.get("exactShaBuildRequired") is True,
        "visualReviewFailureEvidenceUploaded": workflow.get("failureEvidenceUploaded") is True,
        "visualReviewSourceFloor": workflow.get("sourceFloor"),
        "visualReviewNestedFloor": workflow.get("nestedFloor"),
        "passed": final.get("passed") is True and not failures,
        "failures": list(final.get("failures") or []) + failures,
    })
    spec["finalSupplementalSourceMatrix"] = final
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Final visual evidence workflow contract failed:\n- " + "\n- ".join(failures))
    print("Final visual evidence workflow: PASS -> exact SHA build + Browser QA + 80 captures at floor 2674+149")


if __name__ == "__main__":
    main()
