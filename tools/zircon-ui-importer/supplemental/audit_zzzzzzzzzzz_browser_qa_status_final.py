#!/usr/bin/env python3
"""Late final bridge for exact-SHA Browser QA and Visual Review commit-status evidence."""
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
    audit = spec.get("browserQaStatusPublisherAudit") or {}
    failures: list[str] = []

    if final.get("passed") is not True:
        failures.append(f"prior final matrix missing/not PASS: {final}")
    expected = {
        "passed": True,
        "trigger": "push/workflow_dispatch exact-SHA poll",
        "branch": "origins-game-v1",
        "branchSafeWithoutDefaultBranch": True,
        "statusPermissionWrite": True,
        "actionsPermissionRead": True,
        "exactHeadSha": True,
        "exactBrowserQaRunRequired": True,
        "context": "origins/zircon-browser-qa",
        "successMapsToSuccess": True,
        "nonSuccessMapsToFailure": True,
        "timeoutMapsToFailure": True,
        "targetUrlIsWorkflowRun": True,
        "exactVisualReviewRunRequired": True,
        "visualContext": "origins/zircon-visual-review",
        "visualSuccessMapsToSuccess": True,
        "visualNonSuccessMapsToFailure": True,
        "visualTimeoutMapsToFailure": True,
        "visualTargetUrlIsWorkflowRun": True,
        "visualExpectedScreenshots": 80,
        "mutatesSourceContracts": False,
        "runtimePayloadsInvented": False,
        "controlsAdded": 0,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            failures.append(f"QA status publisher drifted: {key}={audit.get(key)!r}, expected {value!r}")

    final.update({
        "browserQaStatusPublisherPassed": audit.get("passed") is True,
        "browserQaStatusContext": audit.get("context"),
        "browserQaStatusExactHeadSha": audit.get("exactHeadSha") is True,
        "browserQaStatusExactRunRequired": audit.get("exactBrowserQaRunRequired") is True,
        "browserQaStatusBranchSafe": audit.get("branchSafeWithoutDefaultBranch") is True,
        "visualReviewStatusContext": audit.get("visualContext"),
        "visualReviewStatusExactRunRequired": audit.get("exactVisualReviewRunRequired") is True,
        "visualReviewStatusExpectedScreenshots": audit.get("visualExpectedScreenshots"),
        "visualReviewStatusTargetUrlIsWorkflowRun": audit.get("visualTargetUrlIsWorkflowRun") is True,
        "qaStatusMutatesSourceContracts": False,
        "qaStatusControlsAdded": 0,
        "passed": final.get("passed") is True and not failures,
        "failures": list(final.get("failures") or []) + failures,
    })
    spec["finalSupplementalSourceMatrix"] = final
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Final QA status publisher contract failed:\n- " + "\n- ".join(failures))
    print("Final QA status publisher: PASS -> exact-SHA Browser QA + Visual Review commit status evidence; source floor promotion remains source-owned")


if __name__ == "__main__":
    main()
