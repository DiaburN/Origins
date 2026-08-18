#!/usr/bin/env python3
"""Correct false `sourceAnonymous` classifications using constructor offsets.

The base lightweight parser can classify `new DX...` as anonymous when the C#
left-hand side is an array/indexer/property expression rather than a simple local
identifier. Source offsets let us distinguish those assignment-backed creations
from genuinely anonymous statements without changing control count, names,
geometry or runtime state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_ui_source_spec import constructor_body  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    corrected: list[dict] = []
    failures: list[str] = []

    for window in spec.get('windows') or []:
        source_path = str(window.get('sourcePath') or '')
        class_name = str(window.get('class') or window.get('sourceClass') or '')
        path = args.zircon_root / source_path
        if not source_path or not class_name or not path.exists():
            continue
        body = constructor_body(path.read_text(encoding='utf-8-sig'), class_name)
        if not body:
            continue

        for control in window.get('controls') or []:
            if control.get('sourceAnonymous') is not True:
                continue
            if control.get('sourceGenerated') is True or control.get('compositeChild') is True:
                continue
            offset = control.get('sourceInitializerOffset')
            if not isinstance(offset, int) or offset < 0 or offset > len(body):
                continue
            prefix = body[:offset].rstrip()
            if not prefix.endswith('='):
                continue

            # The lexical source says this initializer is assigned. Preserve its
            # existing stable manifest name so downstream references do not move;
            # correct provenance only.
            control['sourceAnonymous'] = False
            control['sourceAssignmentBackedInitializer'] = True
            control['sourceAnonymousReclassificationPass'] = 'assignment-backed-v1'
            corrected.append({
                'field': window.get('field'),
                'control': control.get('name'),
                'type': control.get('type'),
                'sourceInitializerOffset': offset,
            })

    # Trade's two `new DXLabel { ... }` captions are the canonical genuinely
    # anonymous constructor controls and must survive this correction untouched.
    trade = next((window for window in spec.get('windows') or [] if window.get('field') == 'TradeBox'), None)
    trade_anonymous = [
        control for control in (trade or {}).get('controls', [])
        if control.get('sourceAnonymous') is True
    ]
    if len(trade_anonymous) != 2 or any(control.get('type') != 'DXLabel' for control in trade_anonymous):
        failures.append(
            'TradeBox genuine anonymous baseline changed after assignment-backed reclassification: '
            f"{[(c.get('name'), c.get('type')) for c in trade_anonymous]}"
        )

    report = {
        'passed': not failures,
        'version': 1,
        'controlsReclassified': len(corrected),
        'controlCountChanged': False,
        'controlNamesChanged': False,
        'geometryChanged': False,
        'runtimePayloadsInvented': False,
        'tradeGenuineAnonymousControls': len(trade_anonymous),
        'corrected': corrected,
        'failures': failures,
    }
    spec['assignmentBackedAnonymousIdentityPass'] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if failures:
        raise SystemExit('Assignment-backed anonymous identity pass failed:\n- ' + '\n- '.join(failures))
    print(
        'Assignment-backed anonymous identity: PASS -> '
        f"{len(corrected)} false anonymous classifications corrected; Trade genuine anonymous=2"
    )


if __name__ == '__main__':
    main()
