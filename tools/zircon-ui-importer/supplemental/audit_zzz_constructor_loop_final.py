#!/usr/bin/env python3
"""Last-pass guard tying constructor-loop coverage into the final matrix."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    loop = spec.get('constructorLoopInventory') or {}
    custom = spec.get('customConstructorLoopInventory') or {}
    final = spec.get('finalSupplementalSourceMatrix') or {}
    failures = []

    if final.get('passed') is not True:
        failures.append(f'prior final supplemental matrix missing/not PASS: {final}')

    if loop.get('passed') is not True or loop.get('version') != 2:
        failures.append(f'constructor loop inventory missing/not v2 PASS: {loop}')
    if loop.get('unexpectedDeterministicLoops') != []:
        failures.append(f'uncovered deterministic constructor loops remain: {loop.get("unexpectedDeterministicLoops")}')
    if loop.get('controlsFabricatedByAudit') is not False or loop.get('runtimePayloadsInvented') is not False:
        failures.append(f'constructor loop audit boundary broken: {loop}')

    if custom.get('passed') is not True or custom.get('version') != 2:
        failures.append(f'custom constructor loop inventory missing/not v2 PASS: {custom}')
    if custom.get('unexpectedDeterministicLoops') != []:
        failures.append(f'uncovered deterministic custom-constructor loops remain: {custom.get("unexpectedDeterministicLoops")}')
    if custom.get('controlsFabricatedByAudit') is not False or custom.get('runtimePayloadsInvented') is not False:
        failures.append(f'custom constructor loop audit boundary broken: {custom}')
    if custom.get('exactLoopSignaturesRequired') is not True:
        failures.append(f'custom constructor exact source signatures are not required: {custom}')

    game_store = custom.get('gameStoreContractRequired') or {}
    expected_store = {
        'controlsAdded': 215,
        'itemRows': 10,
        'topRows': 5,
        'quantityOptionsPerRow': 10,
    }
    if game_store != expected_store:
        failures.append(f'custom constructor GameStore protection drifted: {game_store}, expected {expected_store}')
    protected = set(custom.get('protectedCustomTypes') or [])
    expected_protected = {'GameStoreItemListControl', 'GameStoreTopItemsControl', 'GameStoreItem'}
    if protected != expected_protected:
        failures.append(f'custom constructor protected types drifted: {sorted(protected)}, expected {sorted(expected_protected)}')

    final['constructorLoopInventoryVersion'] = loop.get('version')
    final['constructorControlLoops'] = loop.get('loopCount')
    final['constructorLoopClassifications'] = loop.get('classificationCounts')
    final['unexpectedDeterministicConstructorLoops'] = len(loop.get('unexpectedDeterministicLoops') or [])
    final['customConstructorLoopInventoryVersion'] = custom.get('version')
    final['customConstructorControlLoops'] = custom.get('loopCount')
    final['customConstructorLoopClassifications'] = custom.get('classificationCounts')
    final['unexpectedDeterministicCustomConstructorLoops'] = len(custom.get('unexpectedDeterministicLoops') or [])
    final['customConstructorExactLoopSignaturesRequired'] = custom.get('exactLoopSignaturesRequired')
    final['customConstructorGameStoreContract'] = game_store
    final['passed'] = not failures and final.get('passed') is True
    final['failures'] = list(final.get('failures') or []) + failures
    spec['finalSupplementalSourceMatrix'] = final

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    if failures:
        raise SystemExit('Final constructor-loop coverage failed:\n- ' + '\n- '.join(failures))

    print(
        'Final constructor-loop coverage: PASS -> '
        f'windowLoops={loop.get("loopCount")}, customLoops={custom.get("loopCount")}, '
        'custom inventory v2 exact GameStore signatures protected, unexpected deterministic=0'
    )


if __name__ == '__main__':
    main()
