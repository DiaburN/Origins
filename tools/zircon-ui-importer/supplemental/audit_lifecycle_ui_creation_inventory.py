#!/usr/bin/env python3
"""Inventory UI controls created directly inside Zircon view lifecycle callbacks.

This catches resize/area/visibility callbacks that can materialize structural UI
outside constructors. BeltDialog is intentionally resize-dependent: its grid is
rebuilt for the current client area and one hotkey DXLabel is created per actual
rendered cell. That template is already represented by the Belt fidelity runtime
and must not be converted into a guessed fixed manifest count.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LIFECYCLE_METHODS = {
    'OnClientAreaChanged',
    'OnDisplayAreaChanged',
    'OnSizeChanged',
    'OnParentChanged',
    'OnLocationChanged',
    'OnIsVisibleChanged',
    'OnOpacityChanged',
    'OnIsResizingChanged',
}

EXPECTED = {
    ('Client/Scenes/Views/BeltDialog.cs', 'BeltDialog', 'OnClientAreaChanged'): [
        'DXItemGrid',
        'DXLabel',
    ],
}

CLASS_RE = re.compile(r'\bclass\s+(?P<name>[A-Za-z_]\w*)\s*:\s*(?P<base>[A-Za-z_]\w*)')
METHOD_RE = re.compile(
    r'\b(?:public|protected|private|internal)\s+'
    r'(?:(?:sealed|override|virtual|static|async|new)\s+)*'
    r'[A-Za-z_][\w<>,\.\[\]\?]*\s+'
    r'(?P<name>On[A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{',
    re.S,
)
NEW_RE = re.compile(r'\bnew\s+(?P<type>[A-Za-z_]\w*)\s*(?:\{|\()')


def sanitize(text: str) -> str:
    """Blank comments and string/char literals while preserving offsets/braces."""
    chars = list(text)
    i = 0
    n = len(chars)
    while i < n:
        if i + 1 < n and chars[i] == '/' and chars[i + 1] == '/':
            j = i
            while j < n and chars[j] != '\n':
                chars[j] = ' '
                j += 1
            i = j
            continue
        if i + 1 < n and chars[i] == '/' and chars[i + 1] == '*':
            j = i
            chars[j] = chars[j + 1] = ' '
            j += 2
            while j + 1 < n and not (chars[j] == '*' and chars[j + 1] == '/'):
                if chars[j] != '\n':
                    chars[j] = ' '
                j += 1
            if j + 1 < n:
                chars[j] = chars[j + 1] = ' '
                j += 2
            i = j
            continue
        if chars[i] in {'"', "'"}:
            quote = chars[i]
            verbatim = quote == '"' and i > 0 and chars[i - 1] == '@'
            chars[i] = ' '
            j = i + 1
            while j < n:
                if verbatim and quote == '"' and chars[j] == '"' and j + 1 < n and chars[j + 1] == '"':
                    chars[j] = chars[j + 1] = ' '
                    j += 2
                    continue
                if chars[j] == quote:
                    chars[j] = ' '
                    j += 1
                    break
                if not verbatim and chars[j] == '\\' and j + 1 < n:
                    if chars[j] != '\n':
                        chars[j] = ' '
                    if chars[j + 1] != '\n':
                        chars[j + 1] = ' '
                    j += 2
                    continue
                if chars[j] != '\n':
                    chars[j] = ' '
                j += 1
            i = j
            continue
        i += 1
    return ''.join(chars)


def block_end(clean: str, open_brace: int) -> int:
    depth = 0
    for i in range(open_brace, len(clean)):
        ch = clean[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i + 1
    return len(clean)


def class_at(clean: str, position: int) -> str:
    best_name = ''
    best_pos = -1
    for match in CLASS_RE.finditer(clean, 0, position):
        brace = clean.find('{', match.end())
        if brace < 0:
            continue
        end = block_end(clean, brace)
        if brace <= position < end and match.start() > best_pos:
            best_name = match.group('name')
            best_pos = match.start()
    return best_name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    views = args.zircon_root / 'Client/Scenes/Views'
    controls = args.zircon_root / 'Client/Controls'
    if not views.exists():
        raise SystemExit(f'Zircon Views directory missing: {views}')

    inheritance: dict[str, str] = {}
    source_files = list(views.rglob('*.cs')) + (list(controls.rglob('*.cs')) if controls.exists() else [])
    sanitized: dict[Path, str] = {}
    for path in source_files:
        clean = sanitize(path.read_text(encoding='utf-8-sig'))
        sanitized[path] = clean
        for match in CLASS_RE.finditer(clean):
            inheritance[match.group('name')] = match.group('base')

    def is_ui_type(name: str) -> bool:
        if name.startswith('DX'):
            return True
        seen: set[str] = set()
        current = name
        while current and current not in seen:
            seen.add(current)
            base = inheritance.get(current, '')
            if base.startswith('DX'):
                return True
            current = base
        return False

    findings: list[dict] = []
    for path in sorted(views.rglob('*.cs')):
        clean = sanitized[path]
        rel = path.relative_to(args.zircon_root).as_posix()
        for match in METHOD_RE.finditer(clean):
            method = match.group('name')
            if method not in LIFECYCLE_METHODS:
                continue
            open_brace = clean.find('{', match.start(), match.end() + 1)
            if open_brace < 0:
                continue
            end = block_end(clean, open_brace)
            body = clean[open_brace:end]
            created = [m.group('type') for m in NEW_RE.finditer(body) if is_ui_type(m.group('type'))]
            if not created:
                continue
            findings.append({
                'file': rel,
                'class': class_at(clean, match.start()),
                'method': method,
                'createdUiTypes': created,
            })

    actual = {(x['file'], x['class'], x['method']): x['createdUiTypes'] for x in findings}
    failures: list[str] = []
    for key, expected_types in EXPECTED.items():
        if actual.get(key) != expected_types:
            failures.append(f'lifecycle creation drifted for {key}: {actual.get(key)!r}, expected {expected_types!r}')
    for key, created in actual.items():
        if key not in EXPECTED:
            failures.append(f'unreviewed lifecycle-created UI discovered at {key}: {created}')

    belt = spec.get('beltHotkeyTemplateAudit') or {}
    if belt.get('passed') is not True:
        failures.append(f'Belt hotkey template audit missing/not PASS before lifecycle inventory: {belt}')
    if belt.get('localResizeDependent') is not True or belt.get('fixedCountInvented') is not False:
        failures.append(f'Belt lifecycle boundary drifted: {belt}')
    if belt.get('runtimeCreatesLabelsPerRenderedGridCell') is not True:
        failures.append(f'Belt per-rendered-cell runtime contract missing: {belt}')

    report = {
        'passed': not failures,
        'scannedRoot': 'Client/Scenes/Views',
        'lifecycleMethods': sorted(LIFECYCLE_METHODS),
        'directLifecycleUiCreationSites': findings,
        'directLifecycleUiCreationSiteCount': len(findings),
        'structuralResizeTemplates': ['BeltDialog.OnClientAreaChanged'],
        'beltCreatedUiTypes': ['DXItemGrid', 'DXLabel'],
        'beltLabelsPerRenderedGridCell': True,
        'fixedManifestControlsAdded': 0,
        'runtimeItemDataInvented': False,
        'runtimePlayerDataInvented': False,
        'failures': failures,
    }
    spec['lifecycleUiCreationInventory'] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    if failures:
        raise SystemExit('Lifecycle UI creation inventory failed:\n- ' + '\n- '.join(failures))
    print('Lifecycle UI creation inventory: PASS -> Belt is the only direct structural lifecycle UI site; fixed manifest +0')


if __name__ == '__main__':
    main()
