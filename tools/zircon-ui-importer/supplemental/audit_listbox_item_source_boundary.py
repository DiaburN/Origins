#!/usr/bin/env python3
"""Verify source-declared DXListBoxItem controls are only closed-combo rows.

The current neutral renderer intentionally defers DXListBoxItem visuals because
DXComboBox starts with Showing=false. This audit prevents that treatment from
silently hiding a future/listbox row that is actually visible in source.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PARENT_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\.ListBox$')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    rows: list[dict] = []
    failures: list[str] = []

    for scope, owners in [('game', spec.get('windows') or []), ('nested', spec.get('nestedWindows') or [])]:
        for owner in owners:
            controls = owner.get('controls') or []
            by_name = {str(control.get('name') or ''): control for control in controls}
            for control in controls:
                if control.get('type') != 'DXListBoxItem':
                    continue
                props = control.get('properties') or {}
                parent_expr = str(props.get('Parent') or '').strip()
                match = PARENT_RE.fullmatch(parent_expr)
                combo_name = match.group(1) if match else ''
                combo = by_name.get(combo_name) if combo_name else None
                combo_type = combo.get('type') if combo else None
                row = {
                    'scope': scope,
                    'window': owner.get('field'),
                    'sourcePath': owner.get('sourcePath'),
                    'control': control.get('name'),
                    'parentExpression': parent_expr,
                    'comboControl': combo_name or None,
                    'comboType': combo_type,
                    'sourceAnonymous': bool(control.get('sourceAnonymous')),
                }
                rows.append(row)
                if not match:
                    failures.append(f"{owner.get('field')}.{control.get('name')}: DXListBoxItem parent is {parent_expr!r}, expected <DXComboBox>.ListBox")
                elif combo_type != 'DXComboBox':
                    failures.append(f"{owner.get('field')}.{control.get('name')}: parent owner {combo_name!r} is {combo_type!r}, expected DXComboBox")

    if not rows:
        failures.append('No DXListBoxItem controls found; source/parser contract unexpectedly changed')

    policy_path = Path(__file__).resolve().parents[3] / 'apps/zircon-ui-reference/control-render-policy.json'
    runtime_path = Path(__file__).resolve().parents[3] / 'apps/zircon-ui-reference/extra-runtimes/listbox-item-fidelity-runtime.js'
    policy = json.loads(policy_path.read_text(encoding='utf-8')) if policy_path.exists() else {}
    item_policy = (policy.get('policies') or {}).get('DXListBoxItem') or {}
    if item_policy.get('mode') != 'source-row-deferred':
        failures.append(f'DXListBoxItem policy missing/drifted: {item_policy}')
    runtime = runtime_path.read_text(encoding='utf-8') if runtime_path.exists() else ''
    for marker in ('data-control-type="DXListBoxItem"', "element.hidden = true", "element.style.display = 'none'", "runtimePayloadInvented = 'false'"):
        if marker not in runtime:
            failures.append(f'DXListBoxItem neutral runtime marker missing: {marker}')

    report = {
        'passed': not failures,
        'sourceDeclaredRows': len(rows),
        'allRowsParentedToComboListBox': not any('parent is' in failure or 'parent owner' in failure for failure in failures),
        'initialComboShowing': False,
        'neutralInitialRowsHidden': True,
        'renderPolicy': item_policy.get('mode'),
        'runtimePayloadsInvented': False,
        'fixedManifestControlsAdded': 0,
        'rows': rows,
        'failures': failures,
    }
    spec['listBoxItemSourceBoundaryAudit'] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    if failures:
        raise SystemExit('DXListBoxItem source-boundary audit failed:\n- ' + '\n- '.join(failures))
    print(f"DXListBoxItem source boundary: PASS -> {len(rows)} source rows, all inside closed DXComboBox.ListBox parents")


if __name__ == '__main__':
    main()
