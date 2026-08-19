#!/usr/bin/env python3
"""Promote source-verified ORIGINS spell decisions after the full runtime compiles.

The authored decision files deliberately keep runtimeReady=false until the whole
five-class patch set compiles together. This script produces a generated,
flattened decision manifest for the DB activation gate: every verified spell
with a real MagicType is promoted; source stubs remain disabled.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import re

EXPECTED_ACTIVE = 119
EXPECTED_RUNTIME = 118
EXPECTED_STUBS = 1


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def load_decisions(path: pathlib.Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "includes" not in payload:
        return payload.get("decisions", [])

    result: list[dict] = []
    seen: set[str] = set()
    for include in payload["includes"]:
        child = path.parent / include
        for decision in load_decisions(child):
            key = norm(decision.get("crystalSpell", ""))
            if not key:
                raise RuntimeError(f"Decision without crystalSpell in {child}")
            if key in seen:
                raise RuntimeError(f"Duplicate spell decision: {decision['crystalSpell']}")
            seen.add(key)
            result.append(decision)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    source = load_decisions(args.manifest)
    promoted: list[dict] = []
    runtime_count = 0
    stub_count = 0

    for original in source:
        decision = copy.deepcopy(original)
        if not decision.get("verified"):
            raise RuntimeError(f"Unverified active spell cannot be promoted: {decision.get('crystalSpell')}")

        is_stub = (
            decision.get("executionKind") == "SourceStub"
            or str(decision.get("sourceStatus", "")).startswith("stub_")
        )

        if is_stub:
            decision["runtimeReady"] = False
            decision["overlayReady"] = False
            stub_count += 1
        else:
            if not decision.get("zirconMagicType"):
                raise RuntimeError(
                    f"Verified non-stub spell is missing zirconMagicType: {decision.get('crystalSpell')}"
                )
            decision["runtimeReady"] = True
            decision["overlayReady"] = True
            decision["runtimeValidation"] = "full_five_class_serverlibrary_compile_pass"
            runtime_count += 1

        promoted.append(decision)

    if len(promoted) != EXPECTED_ACTIVE:
        raise RuntimeError(f"Expected {EXPECTED_ACTIVE} active decisions, found {len(promoted)}")
    if runtime_count != EXPECTED_RUNTIME or stub_count != EXPECTED_STUBS:
        raise RuntimeError(
            f"Promotion totals mismatch: runtime={runtime_count}, stubs={stub_count}; "
            f"expected {EXPECTED_RUNTIME}/{EXPECTED_STUBS}"
        )

    payload = {
        "schemaVersion": 1,
        "generatedFrom": str(args.manifest),
        "compileGate": "LibraryCore + ServerLibrary, pinned Zircon, all active ORIGINS patches",
        "activePlayableSpellCount": EXPECTED_ACTIVE,
        "runtimeReadySpellCount": runtime_count,
        "sourceStubCount": stub_count,
        "decisions": promoted,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Compiled magic decisions promoted: {runtime_count} runtime-ready / {stub_count} source stub")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
