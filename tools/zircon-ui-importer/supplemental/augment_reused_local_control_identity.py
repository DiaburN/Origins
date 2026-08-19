#!/usr/bin/env python3
"""Canonicalise reused local DX-control variables by lexical source position.

Zircon constructors often reuse locals such as `panel`, `label` and `icon`.
The flat parser preserves every initializer, but a repeated local name is not a
stable manifest identity and later Parent/Tag/geometry expressions can bind to
the wrong occurrence. This pass gives only true repeated named locals a stable
`__srcNN` identity and rebinds source expressions/post-assignments to the
occurrence active at that exact constructor position. C# discard assignments
(`_ = new DX...`) are creations, not reusable variables, and are deliberately
excluded. The pass creates/removes no controls.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_ui_source_spec import constructor_body, match_brace, split_top_level, strip_leading_comments  # noqa: E402

NAMED_DX_RE = re.compile(
    r"(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*)"
    r"new\s+(?P<type>DX[A-Za-z_][A-Za-z0-9_]*)\s*\{"
)
POST_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*)\.(Location|Size|Index|Visible|LibraryFile|Opacity|ButtonType|Checked)\s*=\s*(.+)$",
    re.S,
)
POST_PROPS = {"Location", "Size", "Index", "Visible", "LibraryFile", "Opacity", "ButtonType", "Checked"}
PREFIX = "reused-local-identity-v1"
DISCARD_NAME = "_"


def initializer_occurrences(body: str) -> list[dict]:
    rows: list[dict] = []
    for match in NAMED_DX_RE.finditer(body):
        opening = body.find("{", match.start())
        try:
            closing = match_brace(body, opening)
        except ValueError:
            continue
        chunk = body[opening + 1:closing]
        init_props: set[str] = set()
        for entry in split_top_level(chunk, ','):
            prop = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", entry, re.S)
            if prop:
                init_props.add(prop.group(1))
        rows.append({
            "sourceName": match.group("name"),
            "type": match.group("type"),
            "offset": match.start(),
            "initializerProperties": init_props,
        })
    counts = Counter(row["sourceName"] for row in rows)
    ordinals: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        name = row["sourceName"]
        ordinals[name] += 1
        row["ordinal"] = ordinals[name]
        row["count"] = counts[name]
        row["canonicalName"] = f"{name}__src{ordinals[name]:02d}" if counts[name] > 1 and name != DISCARD_NAME else name
    return rows


def statement_spans(body: str):
    cursor = 0
    for segment in split_top_level(body, ';'):
        start = cursor
        cursor += len(segment) + 1
        raw = segment.strip()
        if raw:
            yield start, strip_leading_comments(raw)


def active_occurrence(rows_by_name: dict[str, list[dict]], name: str, position: int) -> dict | None:
    rows = rows_by_name.get(name) or []
    active = None
    for row in rows:
        if row["offset"] >= position:
            break
        active = row
    return active


def token_replace(expression: str, source_name: str, canonical: str) -> tuple[str, bool]:
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(source_name)}(?![A-Za-z0-9_])"
    updated, count = re.subn(pattern, canonical, expression)
    return updated, count > 0


def rewrite_expression(expression: str, position: int, repeated: dict[str, list[dict]]) -> tuple[str, int]:
    value = str(expression)
    changes = 0
    for source_name in sorted(repeated, key=len, reverse=True):
        active = active_occurrence(repeated, source_name, position)
        if active is None:
            continue
        value, changed = token_replace(value, source_name, active["canonicalName"])
        changes += int(changed)
    return value, changes


def manifest_candidates(item: dict, source_name: str) -> list[dict]:
    # First execution sees the flat-parser source name. A defensive second run
    # sees canonical sourceName metadata. Generated supplemental controls are not
    # accepted as lexical constructor occurrences.
    direct = [
        control for control in item.get("controls", [])
        if control.get("name") == source_name
        and control.get("sourceAnonymous") is not True
        and not control.get("sourceGenerated")
    ]
    if direct:
        return direct
    canonical = [
        control for control in item.get("controls", [])
        if control.get("sourceName") == source_name
        and control.get("sourceAnonymous") is not True
        and not control.get("sourceGenerated")
    ]
    return sorted(
        canonical,
        key=lambda control: (
            int(control.get("sourceRepeatedOrdinal") or 0),
            int(control.get("sourceInitializerOffset") or -1),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    failures: list[str] = []
    windows_report: list[dict] = []
    repeated_identifiers = 0
    canonicalized_controls = 0
    expression_rebindings = 0
    post_assignment_rebindings = 0
    discarded_initializers_excluded = 0
    single_name_candidate_mismatches_ignored = 0

    for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = item.get("sourcePath")
        class_name = item.get("sourceClass") or item.get("class")
        if not source_path or not class_name:
            continue
        path = args.zircon_root / source_path
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8-sig")
        body = constructor_body(source, str(class_name))
        if not body:
            continue

        occurrences = initializer_occurrences(body)
        if not occurrences:
            continue
        rows_by_name: dict[str, list[dict]] = defaultdict(list)
        for row in occurrences:
            rows_by_name[row["sourceName"]].append(row)

        discarded_initializers_excluded += len(rows_by_name.get(DISCARD_NAME) or [])
        repeated = {
            name: rows
            for name, rows in rows_by_name.items()
            if name != DISCARD_NAME and len(rows) > 1
        }

        mapped: dict[int, dict] = {}
        for source_name, rows in rows_by_name.items():
            if source_name == DISCARD_NAME:
                continue
            candidates = manifest_candidates(item, source_name)

            # This pass is strict only for *reused* named locals. Single-use
            # constructor identifiers may have been materialised/renamed by a
            # later deterministic composite pass; they do not need lexical
            # disambiguation. Preserve best-effort source metadata only when the
            # mapping is unambiguous.
            strict_reuse = source_name in repeated
            if len(candidates) != len(rows):
                if strict_reuse:
                    failures.append(
                        f"{item.get('field') or item.get('id')}: source/manifest reused occurrences for {source_name}: "
                        f"{len(rows)} != {len(candidates)}"
                    )
                else:
                    single_name_candidate_mismatches_ignored += 1
                continue

            for row, control in zip(rows, candidates):
                if control.get("type") != row["type"]:
                    if strict_reuse:
                        failures.append(
                            f"{item.get('field') or item.get('id')}: {source_name}#{row['ordinal']} type "
                            f"{control.get('type')} != {row['type']}"
                        )
                    continue
                mapped[id(row)] = control
                control["sourceName"] = source_name
                control["sourceInitializerOffset"] = row["offset"]
                if strict_reuse:
                    control["name"] = row["canonicalName"]
                    control["sourceRepeatedLocal"] = True
                    control["sourceRepeatedOrdinal"] = row["ordinal"]
                    control["sourceRepeatedCount"] = row["count"]
                    control["sourceIdentityPass"] = PREFIX
                    canonicalized_controls += 1

        if not repeated:
            continue

        for row in occurrences:
            control = mapped.get(id(row))
            if control is None:
                continue
            properties = control.get("properties") or {}
            for prop, expression in list(properties.items()):
                updated, changed = rewrite_expression(str(expression), row["offset"], repeated)
                if changed:
                    properties[prop] = updated
                    expression_rebindings += changed

        posts: dict[tuple[str, str], str] = {}
        for position, statement in statement_spans(body):
            match = POST_RE.match(statement)
            if not match:
                continue
            source_name, prop, expression = match.groups()
            if source_name not in repeated:
                continue
            active = active_occurrence(repeated, source_name, position)
            if active is None:
                continue
            value, changed = rewrite_expression(" ".join(expression.split()), position, repeated)
            posts[(active["canonicalName"], prop)] = value
            expression_rebindings += changed

        for source_name, rows in repeated.items():
            for row in rows:
                control = mapped.get(id(row))
                if control is None:
                    continue
                properties = control.get("properties") or {}
                for prop in POST_PROPS:
                    key = (row["canonicalName"], prop)
                    if prop not in row["initializerProperties"] and key not in posts:
                        properties.pop(prop, None)
                for prop in POST_PROPS:
                    key = (row["canonicalName"], prop)
                    if key in posts:
                        properties[prop] = posts[key]
                        post_assignment_rebindings += 1

        repeated_identifiers += len(repeated)
        windows_report.append({
            "field": item.get("field"),
            "id": item.get("id"),
            "sourceClass": class_name,
            "repeated": {name: len(rows) for name, rows in sorted(repeated.items())},
            "canonicalNames": {
                name: [row["canonicalName"] for row in rows]
                for name, rows in sorted(repeated.items())
            },
        })

    duplicate_windows: dict[str, list[str]] = {}
    for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        names = [str(c.get("name") or "") for c in item.get("controls", []) if c.get("name")]
        dups = sorted(name for name, count in Counter(names).items() if count > 1)
        if dups:
            duplicate_windows[str(item.get("field") or item.get("id"))] = dups
    if duplicate_windows:
        failures.append(f"duplicate control identities remain after lexical canonicalization: {duplicate_windows}")

    report = {
        "passed": not failures,
        "version": 1,
        "windowsWithReusedLocals": len(windows_report),
        "repeatedIdentifiers": repeated_identifiers,
        "controlsCanonicalized": canonicalized_controls,
        "expressionRebindings": expression_rebindings,
        "postAssignmentRebindings": post_assignment_rebindings,
        "discardAssignmentsExcluded": True,
        "discardInitializersExcluded": discarded_initializers_excluded,
        "singleUseIdentifiersStrictlyCanonicalized": False,
        "singleUseCandidateMismatchesIgnored": single_name_candidate_mismatches_ignored,
        "strictScope": "repeated named local variables only",
        "windows": windows_report,
        "duplicateIdentityWindows": duplicate_windows,
        "controlsAdded": 0,
        "controlsRemoved": 0,
        "runtimePayloadsInvented": False,
        "failures": failures,
    }
    spec["reusedLocalControlIdentityPass"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Reused local control identity pass failed:\n- " + "\n- ".join(failures))
    print(
        "Reused local control identity: PASS -> "
        f"{len(windows_report)} windows, {repeated_identifiers} true reused names, "
        f"{canonicalized_controls} controls canonicalized, {expression_rebindings} expressions rebound; "
        f"C# discard initializers excluded={discarded_initializers_excluded}"
    )


if __name__ == "__main__":
    main()
