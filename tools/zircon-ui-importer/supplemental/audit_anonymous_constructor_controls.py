#!/usr/bin/env python3
"""Strict inventory for anonymous `new DX* { ... }` constructor controls.

Only controls whose anonymous initializer offset exists in the owning Zircon
constructor are part of this contract. Supplemental deterministic expansions
can legitimately carry copied source metadata from their own helper/composite
constructors; those controls are not anonymous controls of the owning window
constructor and must not be counted here.

Trade's two Gold captions remain the canonical source smoke. Language
resolution is allowed to replace their render Text with the resolved English
literal, but the original C# expression must remain in sourceTextExpression.
This audit never creates controls or runtime payloads.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_ui_source_spec import constructor_body, object_initializers  # noqa: E402


NEW_DX = re.compile(r"\bnew\s+(DX[A-Za-z_][A-Za-z0-9_]*)\s*\{")


def independent_anonymous_entries(body: str) -> list[dict]:
    """Return lexical anonymous DX initializers in this constructor only."""
    found: list[dict] = []
    ordinals: Counter[str] = Counter()
    for match in NEW_DX.finditer(body):
        prefix = body[:match.start()].rstrip()
        if prefix.endswith("="):
            continue
        type_name = match.group(1)
        ordinals[type_name] += 1
        found.append({
            "type": type_name,
            "offset": match.start(),
            "ordinal": ordinals[type_name],
        })
    return found


def parser_smoke() -> list[str]:
    body = """
        NamedButton = new DXButton
        {
            Parent = this,
            Index = 10,
        };
        new DXLabel
        {
            Parent = this,
            Text = "Anonymous",
        };
        DXControl DeclaredControl = new DXControl
        {
            Parent = this,
        };
        new DXLabel
        {
            Parent = this,
            Text = "Anonymous 2",
        };
    """
    controls = object_initializers(body)
    names = [str(control.get("name") or "") for control in controls]
    types = [str(control.get("type") or "") for control in controls]
    anonymous = [control for control in controls if control.get("sourceAnonymous") is True]
    expected_names = ["NamedButton", "AnonymousDXLabel01", "DeclaredControl", "AnonymousDXLabel02"]
    expected_types = ["DXButton", "DXLabel", "DXControl", "DXLabel"]
    errors: list[str] = []
    if names != expected_names:
        errors.append(f"synthetic parser names mismatch: {names} != {expected_names}")
    if types != expected_types:
        errors.append(f"synthetic parser types mismatch: {types} != {expected_types}")
    if len(anonymous) != 2:
        errors.append(f"synthetic parser anonymous count mismatch: {len(anonymous)} != 2")
    if [control.get("sourceAnonymousOrdinal") for control in anonymous] != [1, 2]:
        errors.append(
            "synthetic parser anonymous ordinals mismatch: "
            f"{[control.get('sourceAnonymousOrdinal') for control in anonymous]} != [1, 2]"
        )
    if any(control.get("sourceAnonymous") for control in (controls[0], controls[2])):
        errors.append("synthetic parser marked assigned controls anonymous")
    return errors


def lexical_manifest_anonymous(window: dict, source_entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split sourceAnonymous manifest controls into lexical-owner vs copied metadata."""
    expected = Counter((row["type"], row["offset"]) for row in source_entries)
    matched: list[dict] = []
    supplemental: list[dict] = []
    for control in window.get("controls", []):
        if control.get("sourceAnonymous") is not True:
            continue
        try:
            key = (str(control.get("type") or ""), int(control.get("sourceInitializerOffset")))
        except (TypeError, ValueError):
            supplemental.append(control)
            continue
        if expected[key] > 0:
            expected[key] -= 1
            matched.append(control)
        else:
            supplemental.append(control)
    return matched, supplemental


def props(control: dict) -> dict:
    return control.get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    smoke_failures = parser_smoke()
    failures: list[str] = list(smoke_failures)
    rows: list[dict] = []
    source_total = 0
    manifest_total = 0
    supplemental_metadata_total = 0
    lexical_by_field: dict[str, list[dict]] = {}

    for window in spec.get("windows", []):
        source_path = str(window.get("sourcePath") or "")
        class_name = str(window.get("class") or "")
        path = args.zircon_root / source_path
        if not source_path or not class_name or not path.exists():
            continue
        source = path.read_text(encoding="utf-8-sig")
        body = constructor_body(source, class_name)
        source_entries = independent_anonymous_entries(body)
        controls, supplemental = lexical_manifest_anonymous(window, source_entries)
        lexical_by_field[str(window.get("field") or "")] = controls

        source_types = [row["type"] for row in source_entries]
        manifest_types = [str(control.get("type") or "") for control in controls]
        source_count = Counter(source_types)
        manifest_count = Counter(manifest_types)
        source_total += len(source_entries)
        manifest_total += len(controls)
        supplemental_metadata_total += len(supplemental)

        names = [str(control.get("name") or "") for control in controls]
        if len(names) != len(set(names)):
            failures.append(f"{window.get('field')}: anonymous internal names are not unique: {names}")
        if source_count != manifest_count:
            failures.append(
                f"{window.get('field')}: anonymous source/manifest type mismatch: "
                f"source={dict(source_count)} manifest={dict(manifest_count)}"
            )

        expected_keys = Counter((row["type"], row["offset"], row["ordinal"]) for row in source_entries)
        manifest_keys = Counter()
        for control in controls:
            name = str(control.get("name") or "")
            type_name = str(control.get("type") or "")
            ordinal = control.get("sourceAnonymousOrdinal")
            offset = control.get("sourceInitializerOffset")
            if not name.startswith(f"Anonymous{type_name}"):
                failures.append(f"{window.get('field')}: unstable anonymous identity {name!r} for {type_name}")
            if not isinstance(ordinal, int) or ordinal < 1:
                failures.append(f"{window.get('field')}: anonymous ordinal missing on {name}")
            if not isinstance(offset, int) or offset < 0:
                failures.append(f"{window.get('field')}: anonymous source offset missing on {name}")
            if isinstance(ordinal, int) and isinstance(offset, int):
                manifest_keys[(type_name, offset, ordinal)] += 1
        if expected_keys != manifest_keys:
            failures.append(
                f"{window.get('field')}: anonymous lexical identity mismatch: "
                f"source={dict(expected_keys)} manifest={dict(manifest_keys)}"
            )

        if source_entries or controls or supplemental:
            rows.append({
                "field": window.get("field"),
                "sourceClass": class_name,
                "sourcePath": source_path,
                "sourceCount": len(source_entries),
                "manifestCount": len(controls),
                "supplementalCopiedAnonymousMetadata": len(supplemental),
                "sourceTypes": dict(source_count),
                "manifestTypes": dict(manifest_count),
                "manifestNames": names,
            })

    # Canonical source smoke: TradeDialog creates exactly two anonymous Gold
    # captions, one for each grid. They are genuine desktop UI, not data rows.
    trade_controls = sorted(
        lexical_by_field.get("TradeBox", []),
        key=lambda control: int(control.get("sourceInitializerOffset", -1)),
    )
    if len(trade_controls) != 2 or any(control.get("type") != "DXLabel" for control in trade_controls):
        failures.append(
            "TradeBox must contain exactly two lexical anonymous DXLabel Gold captions: "
            f"{[(c.get('name'), c.get('type')) for c in trade_controls]}"
        )
    else:
        expected_locations = (
            "new Point(UserGrid.Location.X - 4, UserGrid.Location.Y + UserGrid.Size.Height + 20)",
            "new Point(PlayerGrid.Location.X - 4, UserGrid.Location.Y + UserGrid.Size.Height + 20)",
        )
        expected_expression = "CEnvir.Language.TradeDialogGoldLabel"
        expected_text = str(((spec.get("language") or {}).get("English") or {}).get("TradeDialogGoldLabel") or "")
        if not expected_text:
            failures.append("TradeDialogGoldLabel English source text unresolved")
        rendered_literal = json.dumps(expected_text, ensure_ascii=False)
        for index, control in enumerate(trade_controls):
            p = props(control)
            expected = {
                "AutoSize": "false",
                "Border": "false",
                "Font": "new Font(Config.FontName, CEnvir.FontSize(8F), FontStyle.Bold)",
                "ForeColour": "Color.Goldenrod",
                "DrawFormat": "TextFormatFlags.VerticalCenter | TextFormatFlags.Left",
                "Parent": "this",
                "Location": expected_locations[index],
                "Size": "new Size(63, 15)",
                "IsControl": "false",
            }
            for key, value in expected.items():
                if p.get(key) != value:
                    failures.append(
                        f"TradeBox anonymous Gold {index + 1} source property drifted: "
                        f"{key}={p.get(key)!r}, expected {value!r}"
                    )
            if control.get("sourceTextExpression") != expected_expression:
                failures.append(
                    f"TradeBox anonymous Gold {index + 1} source text provenance drifted: "
                    f"{control.get('sourceTextExpression')!r} != {expected_expression!r}"
                )
            if expected_text and p.get("Text") != rendered_literal:
                failures.append(
                    f"TradeBox anonymous Gold {index + 1} rendered Text drifted: "
                    f"{p.get('Text')!r} != {rendered_literal!r}"
                )
            if expected_text and control.get("resolvedText") != expected_text:
                failures.append(
                    f"TradeBox anonymous Gold {index + 1} resolved text drifted: "
                    f"{control.get('resolvedText')!r} != {expected_text!r}"
                )

    if source_total < 2:
        failures.append(f"Anonymous constructor source inventory regressed below Trade baseline: {source_total} < 2")

    report = {
        "passed": not failures,
        "parserSyntheticSmokePassed": not smoke_failures,
        "sourceAnonymousControls": source_total,
        "manifestAnonymousControls": manifest_total,
        "supplementalCopiedAnonymousMetadataExcluded": supplemental_metadata_total,
        "lexicalOwnerOffsetsRequired": True,
        "languageResolvedTextPreservesSourceExpression": True,
        "windowsWithAnonymousControls": sum(1 for row in rows if row["sourceCount"] or row["manifestCount"]),
        "rows": rows,
        "tradeAnonymousGoldLabels": 2,
        "internalNamesVisibleByDesign": False,
        "controlsFabricatedByAudit": False,
        "runtimePayloadsInvented": False,
        "failures": failures,
    }
    spec["anonymousConstructorControlAudit"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Anonymous constructor control audit failed:\n- " + "\n- ".join(failures))
    print(
        "Anonymous constructor control audit: PASS -> "
        f"{source_total} lexical controls; Trade Gold=2; "
        f"supplemental copied metadata excluded={supplemental_metadata_total}"
    )


if __name__ == "__main__":
    main()
