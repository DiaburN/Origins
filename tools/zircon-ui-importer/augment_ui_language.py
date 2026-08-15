#!/usr/bin/env python3
"""Augment a generated Zircon UI manifest with real English runtime labels.

The visual source uses expressions such as `CEnvir.Language.MenuDialogSettingsButton`.
Those expressions are kept intact for provenance, while this script attaches the
actual EnglishMessages.cs value as `resolvedText` to controls and root metadata.
That lets the reference renderer size labels/buttons using the text Zircon really
shows instead of estimating from internal property names.
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


def parse_messages(path: Path) -> dict[str, str]:
    text = path.read_text(encoding='utf-8-sig')
    return {name: decode_csharp_string(value) for name, value in PROPERTY_RE.findall(text)}


def resolve_expression(expression: object, messages: dict[str, str]) -> str | None:
    if expression is None:
        return None
    match = LANG_REF_RE.search(str(expression))
    if not match:
        return None
    return messages.get(match.group(1))


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
    unresolved_keys: set[str] = set()

    for window in spec.get('windows', []):
        root = window.get('root', {})
        root_candidates = [root.get('Text'), root.get('Title'), root.get('Caption')]
        for candidate in root_candidates:
            resolved = resolve_expression(candidate, messages)
            if resolved is not None:
                window['resolvedText'] = resolved
                break

        for control in window.get('controls', []):
            properties = control.get('properties', {})
            # Prioritise visible text-bearing properties over hints/tooltips.
            candidates = [
                properties.get('Text'),
                properties.get('Label'),
                properties.get('TabButton'),
                properties.get('Title'),
                properties.get('Caption'),
            ]
            resolved = None
            for candidate in candidates:
                resolved = resolve_expression(candidate, messages)
                if resolved is not None:
                    break
            if resolved is not None:
                control['resolvedText'] = resolved
                resolved_controls += 1

            # Track any referenced language keys missing from the English class.
            for value in properties.values():
                for key in LANG_REF_RE.findall(str(value)):
                    if key not in messages:
                        unresolved_keys.add(key)

    spec['language'] = {
        'source': 'Client/Envir/Translations/EnglishMessages.cs',
        'English': messages,
        'messageCount': len(messages),
        'resolvedControlCount': resolved_controls,
        'unresolvedReferencedKeys': sorted(unresolved_keys),
    }
    args.spec.write_text(json.dumps(spec, indent=2), encoding='utf-8')

    print('EnglishMessages parsed:', len(messages))
    print('Controls with resolved visible text:', resolved_controls)
    print('Referenced keys not found:', len(unresolved_keys))
    if unresolved_keys:
        print('Unresolved sample:', sorted(unresolved_keys)[:20])


if __name__ == '__main__':
    main()
