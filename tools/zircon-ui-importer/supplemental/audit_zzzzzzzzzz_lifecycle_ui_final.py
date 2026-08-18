#!/usr/bin/env python3
"""Final bridge for lifecycle-created structural UI coverage."""
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
    audit = spec.get('lifecycleUiCreationInventory') or {}
    failures: list[str] = []

    if final.get('passed') is not True:
        failures.append(f'prior final matrix missing/not PASS: {final}')

    expected = {
        'passed': True,
        'directLifecycleUiCreationSiteCount': 1,
        'structuralResizeTemplates': ['BeltDialog.OnClientAreaChanged'],
        'beltCreatedUiTypes': ['DXItemGrid', 'DXLabel'],
        'beltLabelsPerRenderedGridCell': True,
        'fixedManifestControlsAdded': 0,
        'runtimeItemDataInvented': False,
        'runtimePlayerDataInvented': False,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            failures.append(f'lifecycle UI contract drifted: {key}={audit.get(key)!r}, expected {value!r}')

    sites = audit.get('directLifecycleUiCreationSites') or []
    if sites != [{
        'file': 'Client/Scenes/Views/BeltDialog.cs',
        'class': 'BeltDialog',
        'method': 'OnClientAreaChanged',
        'createdUiTypes': ['DXItemGrid', 'DXLabel'],
    }]:
        failures.append(f'lifecycle UI site inventory drifted: {sites!r}')

    final['lifecycleUiCreationInventoryPassed'] = audit.get('passed') is True
    final['lifecycleUiCreationSites'] = audit.get('directLifecycleUiCreationSiteCount')
    final['lifecycleStructuralResizeTemplates'] = audit.get('structuralResizeTemplates')
    final['lifecycleFixedManifestControlsAdded'] = 0
    final['lifecycleRuntimePayloadsInvented'] = False
    final['passed'] = final.get('passed') is True and not failures
    final['failures'] = list(final.get('failures') or []) + failures
    spec['finalSupplementalSourceMatrix'] = final

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if failures:
        raise SystemExit('Final lifecycle UI contract failed:\n- ' + '\n- '.join(failures))
    print('Final lifecycle UI contract: PASS -> Belt only; resize-driven labels remain outside fixed manifest floor')


if __name__ == '__main__':
    main()
