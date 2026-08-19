#!/usr/bin/env python3
"""Augment a generated Zircon UI manifest with real English runtime labels.

Before language resolution this phase applies source-backed derived UI passes:
- temporal constructor post-assignments for the 65 GameScene windows,
- nested/transient DXWindows,
- DXConfigSection automatic Settings layout.

Running them here ensures all generated/corrected controls receive the same
language resolution and that reused C# locals never corrupt the visual state.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from augment_ui_config_sections import apply as apply_config_sections
from augment_ui_game_post_assignments import apply as apply_game_post_assignments
from augment_ui_nested_windows import apply as apply_nested_windows

PROPERTY_RE = re.compile(
    r'public\s+override\s+string\s+([A-Za-z_][A-Za-z0-9_]*)\s*'
    r'\{\s*get;\s*set;\s*\}\s*=\s*"((?:\\.|[^"\\])*)"\s*;',
    re.S,
)
LANG_REF_RE = re.compile(r'CEnvir\.Language\.([A-Za-z_][A-Za-z0-9_]*)')
VISIBLE_TEXT_KEYS = ('Text', 'Label', 'TabButton', 'Title', 'Caption')


def decode_csharp_string(raw: str) -> str:
    try:
        return json.loads('"' + raw + '"')
    except json.JSONDecodeError:
        return raw.replace(r'\"', '"').replace(r'\\', '\\').replace(r'\n', '\n').replace(r'\r', '\r').replace(r'\t', '\t')


def render_literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def parse_messages(path: Path) -> dict[str, str]:
    text = path.read_text(encoding='utf-8-sig')
    return {name: decode_csharp_string(value) for name, value in PROPERTY_RE.findall(text)}


def resolve_expression(expression: object, messages: dict[str, str]) -> tuple[str, str] | None:
    if expression is None:
        return None
    match = LANG_REF_RE.search(str(expression))
    if not match:
        return None
    key = match.group(1)
    value = messages.get(key)
    return (key, value) if value is not None else None


def augment_properties(owner: dict, properties: dict, messages: dict[str, str]) -> bool:
    for property_name in VISIBLE_TEXT_KEYS:
        expression = properties.get(property_name)
        resolved = resolve_expression(expression, messages)
        if resolved is None:
            continue
        key, value = resolved
        owner['resolvedText'] = value
        owner['resolvedLanguageKey'] = key
        owner['sourceTextProperty'] = property_name
        owner['sourceTextExpression'] = expression
        properties[property_name] = render_literal(value)
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--english-messages', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    zircon_root = args.english_messages.parents[3]

    if 'gameTemporalPostAssignments' not in spec:
        post_report=apply_game_post_assignments(spec,zircon_root)
        print('GameScene temporal post assignments:',post_report.get('assignments',0))
        print('GameScene Locations recovered:',post_report.get('locationsAdded',0))
    if 'nestedWindows' not in spec:
        nested_report = apply_nested_windows(spec, zircon_root)
        print('Nested/transient windows reconstructed before language:', nested_report.get('reconstructedCount', 0))
    if 'configSectionPass' not in spec:
        config_report = apply_config_sections(spec, zircon_root)
        print('Config sections reconstructed before language:', config_report.get('sections', 0))
        print('Config controls source-positioned:', config_report.get('controlsPlaced', 0))

    messages = parse_messages(args.english_messages)
    if not messages:
        raise SystemExit('No EnglishMessages properties were parsed')

    resolved_controls = 0
    resolved_windows = 0
    unresolved_keys: set[str] = set()
    owners = list(spec.get('windows', [])) + list(spec.get('nestedWindows', []))

    for window in owners:
        root = window.get('root', {})
        if augment_properties(window, root, messages):
            resolved_windows += 1
        for control in window.get('controls', []):
            properties = control.get('properties', {})
            if augment_properties(control, properties, messages):
                resolved_controls += 1
            values = list(properties.values())
            if control.get('sourceTextExpression') is not None:
                values.append(control['sourceTextExpression'])
            for value in values:
                for key in LANG_REF_RE.findall(str(value)):
                    if key not in messages:
                        unresolved_keys.add(key)

    spec['language'] = {
        'source': 'Client/Envir/Translations/EnglishMessages.cs',
        'English': messages,
        'messageCount': len(messages),
        'resolvedWindowCount': resolved_windows,
        'resolvedControlCount': resolved_controls,
        'renderPropertiesUseResolvedEnglish': True,
        'sourceExpressionsPreserved': True,
        'includesNestedWindows': True,
        'unresolvedReferencedKeys': sorted(unresolved_keys),
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding='utf-8')

    print('EnglishMessages parsed:', len(messages))
    print('Windows with resolved visible text:', resolved_windows)
    print('Controls with resolved visible text:', resolved_controls)
    print('Referenced keys not found:', len(unresolved_keys))
    if unresolved_keys:
        print('Unresolved sample:', sorted(unresolved_keys)[:20])


if __name__ == '__main__':
    main()
