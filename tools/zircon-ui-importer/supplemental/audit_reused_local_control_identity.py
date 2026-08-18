#!/usr/bin/env python3
"""Strict audit for lexical identities of reused local DX controls."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_ui_source_spec import constructor_body  # noqa: E402

NAMED_DX_RE = re.compile(
    r"(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*)"
    r"new\s+(?P<type>DX[A-Za-z_][A-Za-z0-9_]*)\s*\{"
)


def props(control):
    return (control or {}).get("properties") or {}


def source_repeats(body: str) -> dict[str, list[tuple[int, str]]]:
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for match in NAMED_DX_RE.finditer(body):
        grouped[match.group("name")].append((match.start(), match.group("type")))
    return {name: rows for name, rows in grouped.items() if len(rows) > 1}


def require(failures, condition, message):
    if not condition:
        failures.append(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    pass_report = spec.get("reusedLocalControlIdentityPass") or {}
    failures: list[str] = []
    require(failures, pass_report.get("passed") is True, f"identity pass missing/not PASS: {pass_report}")
    require(failures, pass_report.get("version") == 1, f"identity pass version drifted: {pass_report}")
    require(failures, pass_report.get("controlsAdded") == 0 and pass_report.get("controlsRemoved") == 0, f"identity pass changed control count: {pass_report}")
    require(failures, pass_report.get("runtimePayloadsInvented") is False, f"identity pass invented runtime payloads: {pass_report}")
    require(failures, pass_report.get("duplicateIdentityWindows") == {}, f"identity pass left duplicate names: {pass_report}")

    audited_windows = 0
    audited_identifiers = 0
    audited_controls = 0

    for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = item.get("sourcePath")
        class_name = item.get("class") or item.get("sourceClass")
        if not source_path or not class_name:
            continue
        path = args.zircon_root / source_path
        if not path.exists():
            continue
        body = constructor_body(path.read_text(encoding="utf-8-sig"), str(class_name))
        repeats = source_repeats(body)
        if not repeats:
            continue
        audited_windows += 1
        controls = item.get("controls") or []
        for source_name, source_rows in repeats.items():
            audited_identifiers += 1
            manifest_rows = sorted(
                [c for c in controls if c.get("sourceName") == source_name and c.get("sourceRepeatedLocal") is True],
                key=lambda c: int(c.get("sourceRepeatedOrdinal") or 0),
            )
            require(
                failures,
                len(manifest_rows) == len(source_rows),
                f"{item.get('field') or item.get('id')}: {source_name} source/manifest reuse count {len(source_rows)} != {len(manifest_rows)}",
            )
            for ordinal, ((offset, type_name), control) in enumerate(zip(source_rows, manifest_rows), start=1):
                audited_controls += 1
                expected_name = f"{source_name}__src{ordinal:02d}"
                require(failures, control.get("name") == expected_name, f"{item.get('field')}: {source_name}#{ordinal} name {control.get('name')!r} != {expected_name!r}")
                require(failures, control.get("type") == type_name, f"{item.get('field')}: {expected_name} type {control.get('type')!r} != {type_name!r}")
                require(failures, control.get("sourceInitializerOffset") == offset, f"{item.get('field')}: {expected_name} offset {control.get('sourceInitializerOffset')!r} != {offset}")
                require(failures, control.get("sourceRepeatedOrdinal") == ordinal, f"{item.get('field')}: {expected_name} ordinal drifted")
                require(failures, control.get("sourceRepeatedCount") == len(source_rows), f"{item.get('field')}: {expected_name} repeated count drifted")

    duplicate_windows = {}
    for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        names = [str(c.get("name") or "") for c in item.get("controls", []) if c.get("name")]
        dups = sorted(name for name, count in Counter(names).items() if count > 1)
        if dups:
            duplicate_windows[str(item.get("field") or item.get("id"))] = dups
    require(failures, duplicate_windows == {}, f"duplicate manifest identities remain: {duplicate_windows}")

    # Canonical smoke for the source pattern that exposed the bug.
    monster = next((w for w in spec.get("windows", []) if w.get("field") == "MonsterBox"), None)
    require(failures, monster is not None, "MonsterBox missing")
    if monster is not None:
        controls = monster.get("controls") or []
        by_name = {str(c.get("name") or ""): c for c in controls}
        source_counts = Counter(str(c.get("sourceName") or "") for c in controls if c.get("sourceRepeatedLocal") is True)
        require(failures, source_counts.get("panel") == 3, f"Monster panel reuse != 3: {source_counts}")
        require(failures, source_counts.get("label") == 3, f"Monster label reuse != 3: {source_counts}")
        require(failures, source_counts.get("icon") == 8, f"Monster icon reuse != 8: {source_counts}")
        require(failures, props(by_name.get("LevelLabel")).get("Parent") == "panel__src01", f"Monster LevelLabel lexical parent drifted: {props(by_name.get('LevelLabel'))}")
        require(failures, props(by_name.get("NameLabel")).get("Parent") == "panel__src02", f"Monster NameLabel lexical parent drifted: {props(by_name.get('NameLabel'))}")
        require(failures, props(by_name.get("FireResistLabel")).get("Tag") == "icon__src01", f"Monster Fire tag drifted: {props(by_name.get('FireResistLabel'))}")
        require(failures, props(by_name.get("PhysicalResistLabel")).get("Tag") == "icon__src08", f"Monster Physical tag drifted: {props(by_name.get('PhysicalResistLabel'))}")
        expected_locations = {
            "label__src01": "new Point(36 - label__src01.Size.Width, 5)",
            "label__src02": "new Point(125 - label__src02.Size.Width, 5)",
            "label__src03": "new Point(36 - label__src03.Size.Width, 22)",
        }
        for name, expected in expected_locations.items():
            require(failures, props(by_name.get(name)).get("Location") == expected, f"Monster {name} post Location drifted: {props(by_name.get(name))}")

    report = {
        "passed": not failures,
        "version": 1,
        "windowsWithReusedLocals": audited_windows,
        "repeatedIdentifiers": audited_identifiers,
        "reusedControls": audited_controls,
        "allManifestIdentitiesUnique": duplicate_windows == {},
        "monsterLexicalSmokePassed": not any("Monster" in failure for failure in failures),
        "controlsFabricatedByAudit": False,
        "runtimePayloadsInvented": False,
        "failures": failures,
    }
    spec["reusedLocalControlIdentityAudit"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Reused local control identity audit failed:\n- " + "\n- ".join(failures))
    print(
        "Reused local control identity audit: PASS -> "
        f"{audited_windows} windows, {audited_identifiers} reused identifiers, {audited_controls} controls; Monster lexical smoke PASS"
    )


if __name__ == "__main__":
    main()
