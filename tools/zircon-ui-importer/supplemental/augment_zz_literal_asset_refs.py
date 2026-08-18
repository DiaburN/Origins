#!/usr/bin/env python3
"""Refresh literal assetRefs after all supplemental UI augmenters.

Supplemental passes can materialise source-backed controls after the base parser
has already collected its asset reference set. Walk the final augmented windows
and promote only literal LibraryFile + Index/BaseIndex references. Symbolic or
runtime indices are deliberately ignored so this pass cannot invent artwork.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


LIBRARY_RE = re.compile(r"\bLibraryFile\.([A-Za-z_][A-Za-z0-9_]*)\b")
INT_RE = re.compile(r"^-?\d+$")


def literal_int(value) -> int | None:
    text = str(value or "").strip()
    return int(text) if INT_RE.fullmatch(text) else None


def library_name(value) -> str | None:
    match = LIBRARY_RE.search(str(value or ""))
    return match.group(1) if match else None


def collect_from_properties(properties: dict, found: dict[str, set[int]]) -> None:
    for key, raw_library in properties.items():
        if not str(key).endswith("LibraryFile"):
            continue
        prefix = str(key)[:-len("LibraryFile")]
        library = library_name(raw_library)
        if not library:
            continue

        index = literal_int(properties.get(prefix + "Index"))
        if index is not None and index >= 0:
            found[library].add(index)

        base = literal_int(properties.get(prefix + "BaseIndex"))
        if base is None or base < 0:
            continue
        count = literal_int(properties.get(prefix + "FrameCount"))
        if count is not None and count > 0:
            found[library].update(range(base, base + count))
        else:
            found[library].add(base)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    found: dict[str, set[int]] = defaultdict(set)

    for window in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        collect_from_properties(window.get("root") or {}, found)
        for control in window.get("controls") or []:
            collect_from_properties(control.get("properties") or {}, found)

    refs = spec.setdefault("assetRefs", {})
    added: dict[str, list[int]] = {}
    total_added = 0
    for library, values in sorted(found.items()):
        existing = {int(value) for value in refs.get(library, [])}
        new_values = sorted(values - existing)
        if new_values:
            added[library] = new_values
            total_added += len(new_values)
        refs[library] = sorted(existing | values)

    # Current deterministic row source requires these exact literal artwork
    # references. Assert discovery rather than hard-injecting them.
    required = {
        "GameInter": {3624, 6570},
        "Interface": {60, 61, 62},
    }
    missing = {
        library: sorted(values - set(int(value) for value in refs.get(library, [])))
        for library, values in required.items()
    }
    missing = {library: values for library, values in missing.items() if values}
    if missing:
        raise SystemExit(f"Literal supplemental asset discovery incomplete: {missing}")

    spec["supplementalLiteralAssetRefPass"] = {
        "passed": True,
        "literalRefsObserved": sum(len(values) for values in found.values()),
        "refsAdded": total_added,
        "addedByLibrary": added,
        "requiredDeterministicRowRefsPresent": True,
        "symbolicRuntimeRefsInvented": False,
        "source": "final supplemental control/root literal LibraryFile + Index/BaseIndex properties",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Supplemental literal asset refs: PASS -> "
        f"observed={sum(len(values) for values in found.values())}; added={total_added}; libraries={len(found)}"
    )


if __name__ == "__main__":
    main()
