#!/usr/bin/env python3
"""Late final bridge for source-declared DXListBoxItem handling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    final = spec.get('finalSupplementalSourceMatrix') or {}
    audit = spec.get('listBoxItemSourceBoundaryAudit') or {}
    failures: list[str] = []

    if final.get('passed') is not True:
        failures.append(f'prior final matrix missing/not PASS: {final}')

    expected = {
        'passed': True,
        'allRowsParentedToComboListBox': True,
        'initialComboShowing': False,
        'neutralInitialRowsHidden': True,
        'renderPolicy': 'source-row-deferred',
        'runtimePayloadsInvented': False,
        'fixedManifestControlsAdded': 0,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            failures.append(f'DXListBoxItem source boundary drifted: {key}={audit.get(key)!r}, expected {value!r}')
    if int(audit.get('sourceDeclaredRows') or 0) <= 0:
        failures.append(f'DXListBoxItem source row inventory is empty: {audit}')

    final['listBoxItemSourceBoundaryPassed'] = audit.get('passed') is True
    final['listBoxItemSourceRows'] = audit.get('sourceDeclaredRows')
    final['listBoxItemAllComboRows'] = audit.get('allRowsParentedToComboListBox') is True
    final['listBoxItemInitialState'] = 'closed-combo-deferred'
    final['listBoxItemFixedManifestControlsAdded'] = 0
    final['listBoxItemRuntimePayloadsInvented'] = False
    final['passed'] = final.get('passed') is True and not failures
    final['failures'] = list(final.get('failures') or []) + failures
    spec['finalSupplementalSourceMatrix'] = final

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if failures:
        raise SystemExit('Final DXListBoxItem boundary contract failed:\n- ' + '\n- '.join(failures))
    print(f"Final DXListBoxItem boundary: PASS -> {audit.get('sourceDeclaredRows')} source rows; closed combo state; fixed floor +0")


if __name__ == '__main__':
    main()
