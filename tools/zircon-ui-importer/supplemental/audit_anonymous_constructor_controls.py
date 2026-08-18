#!/usr/bin/env python3
"""Strict inventory for anonymous `new DX* { ... }` constructor controls.

Zircon sometimes creates deterministic controls without assigning them to a
field/local (Trade's two Gold captions are the canonical example). The base
parser marks these controls `sourceAnonymous`. This audit independently scans
current source constructors, compares source/manifest counts by type, locks the
source-exact Trade captions, and exercises the parser with a synthetic mixed
named/anonymous constructor body. It never creates controls in the manifest.
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


def independent_anonymous_types(body: str) -> list[str]:
    """Count source `new DX*` initializers with no assignment immediately before.

    This is deliberately independent of object_initializers(). Named controls
    end in `= new DX...`; anonymous statements do not. The scan is constructor-
    scoped, so methods such as Trade's click-created amount window are excluded.
    """
    found: list[str] = []
    for match in NEW_DX.finditer(body):
        prefix = body[:match.start()].rstrip()
        if prefix.endswith("="):
            continue
        found.append(match.group(1))
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


def manifest_anonymous(window: dict) -> list[dict]:
    return [control for control in window.get("controls", []) if control.get("sourceAnonymous") is True]


def props(control: dict) -> dict:
    return control.get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    rows: list[dict] = []
    failures: list[str] = parser_smoke()
    source_total = 0
    manifest_total = 0

    for window in spec.get("windows", []):
        source_path = str(window.get("sourcePath") or "")
        class_name = str(window.get("class") or "")
        path = args.zircon_root / source_path
        if not source_path or not class_name or not path.exists():
            continue
        source = path.read_text(encoding="utf-8-sig")
        body = constructor_body(source, class_name)
        source_types = independent_anonymous_types(body)
        controls = manifest_anonymous(window)
        manifest_types = [str(control.get("type") or "") for control in controls]
        source_count = Counter(source_types)
        manifest_count = Counter(manifest_types)
        source_total += len(source_types)
        manifest_total += len(controls)

        names = [str(control.get("name") or "") for control in controls]
        if len(names) != len(set(names)):
            failures.append(f"{window.get('field')}: anonymous internal names are not unique: {names}")
        if source_count != manifest_count:
            failures.append(
                f"{window.get('field')}: anonymous source/manifest type mismatch: "
                f"source={dict(source_count)} manifest={dict(manifest_count)}"
            )
        for control in controls:
            name = str(control.get("name") or "")
            type_name = str(control.get("type") or "")
            if not name.startswith(f"Anonymous{type_name}"):
                failures.append(f"{window.get('field')}: unstable anonymous identity {name!r} for {type_name}")
            if not isinstance(control.get("sourceAnonymousOrdinal"), int) or int(control["sourceAnonymousOrdinal"]) < 1:
                failures.append(f"{window.get('field')}: anonymous ordinal missing on {name}")
            if not isinstance(control.get("sourceInitializerOffset"), int) or int(control["sourceInitializerOffset"]) < 0:
                failures.append(f"{window.get('field')}: anonymous source offset missing on {name}")

        if source_types or controls:
            rows.append({
                "field": window.get("field"),
                "sourceClass": class_name,
                "sourcePath": source_path,
                "sourceCount": len(source_types),
                "manifestCount": len(controls),
                "sourceTypes": dict(source_count),
                "manifestTypes": dict(manifest_count),
                "manifestNames": names,
            })

    # Canonical source smoke: TradeDialog creates exactly two anonymous Gold
    # captions, one for each grid. They are genuine desktop UI, not data rows.
    trade = next((window for window in spec.get("windows", []) if window.get("field") == "TradeBox"), None)
    if trade is None:
        failures.append("TradeBox missing from manifest")
    else:
        trade_controls = sorted(
            manifest_anonymous(trade),
            key=lambda control: int(control.get("sourceInitializerOffset", -1)),
        )
        if len(trade_controls) != 2 or any(control.get("type") != "DXLabel" for control in trade_controls):
            failures.append(
                f"TradeBox must contain exactly two anonymous DXLabel Gold captions: "
                f"{[(c.get('name'), c.get('type')) for c in trade_controls]}"
            )
        else:
            expected_locations = (
                "new Point(UserGrid.Location.X - 4, UserGrid.Location.Y + UserGrid.Size.Height + 20)",
                "new Point(PlayerGrid.Location.X - 4, UserGrid.Location.Y + UserGrid.Size.Height + 20)",
            )
            expected_text = str(((spec.get("language") or {}).get("English") or {}).get("TradeDialogGoldLabel") or "")
            if not expected_text:
                failures.append("TradeDialogGoldLabel English source text unresolved")
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
                    "Text": "CEnvir.Language.TradeDialogGoldLabel",
                    "Size": "new Size(63, 15)",
                    "IsControl": "false",
                }
                for key, value in expected.items():
                    if p.get(key) != value:
                        failures.append(
                            f"TradeBox anonymous Gold {index + 1} source property drifted: "
                            f"{key}={p.get(key)!r}, expected {value!r}"
                        )
                if expected_text and control.get("resolvedText") != expected_text:
                    failures.append(
                        f"TradeBox anonymous Gold {index + 1} runtime text unresolved: "
                        f"{control.get('resolvedText')!r} != {expected_text!r}"
                    )

    if source_total < 2:
        failures.append(f"Anonymous constructor source inventory regressed below Trade baseline: {source_total} < 2")

    report = {
        "passed": not failures,
        "parserSyntheticSmokePassed": not parser_smoke(),
        "sourceAnonymousControls": source_total,
        "manifestAnonymousControls": manifest_total,
        "windowsWithAnonymousControls": len(rows),
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
        f"{source_total} controls across {len(rows)} GameScene windows; Trade Gold=2"
    )


if __name__ == "__main__":
    main()
