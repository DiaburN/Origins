#!/usr/bin/env python3
"""Augment a generated Zircon UI manifest with real English runtime labels.

The visual source uses expressions such as `CEnvir.Language.MenuDialogSettingsButton`.
Those expressions remain available as provenance while this script attaches the
actual EnglishMessages.cs value and prepares a render-facing copy of the relevant
text property. The source C# itself is never modified.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROPERTY_RE = re.compile(
    r'public\s+override\s+string\s+([A-Za-z_][A-Za-z0-9_]*)\s*'
    r'\{\s*get;\s*set;\s*\}\s*=\s*"((?:\\.|[^"\\])*)"\s*;',
    re.S,
)
LANG_REF_RE = re.compile(r'CEnvir\.Language\.([A-Za-z_][A-Za-z0-9_]*)')
VISIBLE_TEXT_KEYS = ('Text', 'Label', 'TabButton', 'Title', 'Caption')


def decode_csharp_string(raw: str) -> str:
    # The current EnglishMessages file uses standard C# escape sequences that
    # overlap with JSON for the strings relevant to UI labels.
    try:
        return json.loads('"' + raw + '"')
    except json.JSONDecodeError:
        return (
            raw.replace(r'\"', '"')
               .replace(r'\\', '\\')
               .replace(r'\n', '\n')
               .replace(r'\r', '\r')
               .replace(r'\t', '\t')
        )


def render_literal(value: str) -> str:
    """Return a JSON/C#-compatible quoted literal for the browser manifest."""
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
    if value is None:
        return None
    return key, value


def augment_properties(owner: dict, properties: dict, messages: dict[str, str]) -> bool:
    """Resolve the first visible language property and preserve its source expression.

    The generated manifest is a derived artifact, so replacing its render-facing
    property is safe as long as provenance is kept explicitly. This makes the
    existing renderer and geometry resolver consume the same text Zircon displays.
    """
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
    messages = parse_messages(args.english_messages)
    if not messages:
        raise SystemExit('No EnglishMessages properties were parsed')

    resolved_controls = 0
    resolved_windows = 0
    unresolved_keys: set[str] = set()

    for window in spec.get('windows', []):
        root = window.get('root', {})
        if augment_properties(window, root, messages):
            resolved_windows += 1

        for control in window.get('controls', []):
            properties = control.get('properties', {})
            if augment_properties(control, properties, messages):
                resolved_controls += 1

            # Search both the derived properties and preserved source expression.
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
