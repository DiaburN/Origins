#!/usr/bin/env python3
"""Reconstruct DXConfigSection automatic Settings layout from Zircon source.

DXConfigWindow creates many controls without Location/Parent and then places them
through DXConfigSection.AddControl()/DXConfigTab.AddSection(). A flat initializer
parser cannot see that geometry. This pass reproduces those source algorithms:
- section width 348
- header 25, control rows 20, footer 5
- one/two-column alignment rules by control type
- cumulative AddSection vertical stacking per tab
- 4750/4751/4752 section artwork and section/control labels

It also imports controls that Zircon constructs with target-typed/no-initializer
syntax (for example `SoundPlayerBar = new();` and `new DXColourControlPair()`) but
ONLY when the source passes that named field to a recognized AddControl call.
No runtime combo items, monitor modes or live player/config data are invented.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from build_ui_source_spec import constructor_body, match_brace, split_top_level

# Supports both target-typed `new(...)` and explicit `new DXConfigSection(...)`.
SECTION_RE = re.compile(
    r"\bDXConfigSection\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
    r"new(?:\s+DXConfigSection)?\s*\((.*?)\)\s*\{",
    re.S,
)
CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.(AddControl|AddSection)\s*\(", re.S)
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
FIELD_DECL_RE = re.compile(
    r"\b(?:public|private|protected|internal)\s+(DX[A-Za-z_][A-Za-z0-9_]*)\s+([^;]+);",
    re.S,
)

SECTION_WIDTH = 348
HEADER_HEIGHT = 25
CONTROL_HEIGHT = 20
FOOTER_HEIGHT = 5


def normalise(value: str) -> str:
    return " ".join(value.strip().split())


def find_matching_paren(text: str, opening: int) -> int:
    """Return the closing paren while respecting strings/chars/comments."""
    depth = 0
    in_string = False
    verbatim = False
    in_char = False
    escaped = False
    line_comment = False
    block_comment = False
    i = opening
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if c == "\n": line_comment = False
            i += 1; continue
        if block_comment:
            if c == "*" and n == "/": block_comment = False; i += 2; continue
            i += 1; continue
        if in_char:
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == "'": in_char = False
            i += 1; continue
        if in_string:
            if verbatim:
                if c == '"':
                    if n == '"': i += 2; continue
                    in_string = False; verbatim = False
            else:
                if escaped: escaped = False
                elif c == "\\": escaped = True
                elif c == '"': in_string = False
            i += 1; continue
        if c == "/" and n == "/": line_comment = True; i += 2; continue
        if c == "/" and n == "*": block_comment = True; i += 2; continue
        if c == '@' and n == '"': in_string = True; verbatim = True; i += 2; continue
        if c == '"': in_string = True; i += 1; continue
        if c == "'": in_char = True; i += 1; continue
        if c == "(": depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0: return i
        i += 1
    raise ValueError("unbalanced parentheses")


def parse_initializer_props(body: str, opening: int) -> dict[str, str]:
    closing = match_brace(body, opening)
    chunk = body[opening + 1:closing]
    props: dict[str, str] = {}
    for entry in split_top_level(chunk, ','):
        match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$", entry, re.S)
        if match:
            props[match.group(1)] = normalise(match.group(2))
    return props


def parse_sections(body: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for match in SECTION_RE.finditer(body):
        name, title = match.groups()
        opening = body.find('{', match.start())
        props = parse_initializer_props(body, opening)
        columns_raw = props.get('Columns', '1')
        try: columns = int(columns_raw)
        except ValueError: columns = 1
        result[name] = {
            'name': name,
            'title': normalise(title),
            'columns': max(1, columns),
            'declaredParent': props.get('Parent'),
            'controls': [],
            'tab': None,
            'sectionY': 0,
            'sourceOffset': match.start(),
        }
    return result


def scan_calls(body: str, sections: dict[str, dict]) -> list[dict]:
    """Scan calls directly so foreach/if blocks cannot swallow a later call."""
    calls: list[dict] = []
    for match in CALL_RE.finditer(body):
        owner, method = match.groups()
        opening = body.find('(', match.start())
        try: closing = find_matching_paren(body, opening)
        except ValueError: continue
        args_text = body[opening + 1:closing]
        args = [normalise(arg) for arg in split_top_level(args_text, ',')]
        calls.append({'offset': match.start(), 'owner': owner, 'method': method, 'args': args})

        if method == 'AddControl' and owner in sections and len(args) == 2:
            label_expr, control_expr = args
            if IDENT_RE.fullmatch(control_expr):
                sections[owner]['controls'].append({
                    'label': label_expr,
                    'control': control_expr,
                    'sourceOffset': match.start(),
                })
    return calls


def finish_section_geometry(sections: dict[str, dict], calls: list[dict]) -> None:
    heights: dict[str, int] = {}
    for name, section in sections.items():
        rows = math.ceil(len(section['controls']) / section['columns']) if section['controls'] else 0
        heights[name] = HEADER_HEIGHT + rows * CONTROL_HEIGHT + FOOTER_HEIGHT
        section['rows'] = rows
        section['height'] = heights[name]

    cursor_by_tab: dict[str, int] = {}
    for call in sorted(calls, key=lambda row: row['offset']):
        if call['method'] != 'AddSection' or len(call['args']) != 1:
            continue
        tab = call['owner']
        section_name = call['args'][0]
        if section_name not in sections:
            continue
        section = sections[section_name]
        y = cursor_by_tab.get(tab, 0)
        section['tab'] = tab
        section['sectionY'] = y
        cursor_by_tab[tab] = y + heights[section_name]


def parse_field_types(source: str, class_name: str) -> dict[str, str]:
    ctor_marker = re.search(rf"\bpublic\s+{re.escape(class_name)}\s*\(", source)
    prefix = source[:ctor_marker.start()] if ctor_marker else source
    result: dict[str, str] = {}
    for control_type, names_blob in FIELD_DECL_RE.findall(prefix):
        for raw in split_top_level(names_blob, ','):
            name = raw.split('=', 1)[0].strip()
            if IDENT_RE.fullmatch(name):
                result[name] = control_type
    return result


def imported_control(name: str, source_type: str) -> dict | None:
    provenance = {
        'targetTypedConfigControl': True,
        'sourceType': source_type,
        'sourceConstruction': 'field declaration + DXConfigSection.AddControl source relationship',
    }
    if source_type == 'DXSoundBar':
        return {
            'name': name, 'type': 'DXSoundBar', **provenance,
            'properties': {'Size': 'new Size(180, 18)'},
        }
    if source_type == 'DXColourControlPair':
        return {
            'name': name, 'type': 'DXControl', **provenance,
            'properties': {
                'Size': 'new Size(40, 16)',
                'Border': 'true',
                'BorderColour': 'Constants.PrimaryColour',
            },
        }
    # Keep this conservative. Add new exact source defaults deliberately if
    # future public Zircon introduces another target-typed section control.
    return None


def ensure_section_controls(window: dict, sections: dict[str, dict], source: str) -> dict:
    field_types = parse_field_types(source, window['class'])
    existing = {c.get('name') for c in window.get('controls', [])}
    requested = []
    for section in sections.values():
        requested.extend(row['control'] for row in section['controls'])

    imported: list[dict] = []
    unresolved: list[dict] = []
    for name in dict.fromkeys(requested):
        if name in existing:
            continue
        source_type = field_types.get(name)
        control = imported_control(name, source_type) if source_type else None
        if control:
            window['controls'].append(control)
            existing.add(name)
            imported.append(control)
        else:
            unresolved.append({'name': name, 'fieldType': source_type})
    return {'imported': imported, 'unresolved': unresolved, 'fieldTypes': field_types}


def synthetic_image(name: str, parent: str, index: int, location: str) -> dict:
    return {
        'name': name,
        'type': 'DXImageControl',
        'syntheticSourceControl': 'DXConfigSection',
        'properties': {
            'Parent': parent,
            'LibraryFile': 'LibraryFile.GameInter',
            'Index': str(index),
            'Location': location,
            'IsControl': 'false',
            'PassThrough': 'true',
        },
    }


def synthetic_label(name: str, parent: str, text: str, location: str, size: str | None = None, title: bool = False) -> dict:
    props = {
        'Parent': parent,
        'Text': text,
        'Location': location,
        'ForeColour': 'Color.FromArgb(169, 124, 67)' if not title else 'Color.White',
        'Outline': 'true' if not title else 'false',
        'IsControl': 'false',
    }
    if size:
        props['Size'] = size
        props['AutoSize'] = 'false'
    return {
        'name': name,
        'type': 'DXLabel',
        'syntheticSourceControl': 'DXConfigSection',
        'properties': props,
    }


def synthetic_colour_pair_children(pair: dict, tab: str) -> list[dict]:
    """Flatten DXColourControlPair's exact two 20x16 children onto the same tab.

    Flattening keeps tab visibility correct in the browser's flat DOM while the
    location expressions still derive from the pair's resolved source position.
    """
    name = pair['name']
    base = {
        'type': 'DXColourControl',
        'syntheticSourceControl': 'DXColourControlPair',
        'sourceType': 'DXColourControl',
    }
    fore = {
        'name': f'{name}__ForeColourControl', **base,
        'properties': {
            'Parent': tab,
            'Location': f'new Point({name}.Location.X, {name}.Location.Y)',
            'Size': 'new Size(20, 16)',
        },
    }
    back = {
        'name': f'{name}__BackColourControl', **base,
        'properties': {
            'Parent': tab,
            'Location': f'new Point({name}.Location.X + 20, {name}.Location.Y)',
            'Size': 'new Size(20, 16)',
            'AllowNoColour': 'true',
        },
    }
    return [fore, back]


def is_blank_label(expression: str) -> bool:
    return expression.strip() in {'""', 'string.Empty', 'String.Empty'}


def add_section_artwork(section: dict) -> list[dict]:
    tab = section['tab']
    if not tab: return []
    prefix = f"ConfigSection__{section['name']}"
    y = section['sectionY']
    rows = section['rows']
    body_count = rows * 5
    out: list[dict] = []

    header_name = f"{prefix}__Header"
    body0_name = f"{prefix}__Body__1"
    out.append(synthetic_image(header_name, tab, 4750, f"new Point(0, {y})"))
    for i in range(body_count):
        name = f"{prefix}__Body__{i + 1}"
        location = (
            f"new Point(0, {y} + {header_name}.Size.Height)" if i == 0 else
            f"new Point(0, {y} + {header_name}.Size.Height + {i} * {body0_name}.Size.Height)"
        )
        out.append(synthetic_image(name, tab, 4751, location))
    footer_name = f"{prefix}__Footer"
    footer_location = (
        f"new Point(0, {y} + {header_name}.Size.Height + {body_count} * {body0_name}.Size.Height)" if body_count else
        f"new Point(0, {y} + {header_name}.Size.Height)"
    )
    out.append(synthetic_image(footer_name, tab, 4752, footer_location))
    out.append(synthetic_label(
        f"{prefix}__Title", tab, section['title'], f"new Point(0, {y})",
        f"new Size({SECTION_WIDTH}, 20)", title=True,
    ))
    return out


def placement(section: dict, control: dict, item_index: int) -> tuple[str, str]:
    columns = section['columns']
    y = section['sectionY'] + HEADER_HEIGHT
    ctype = control.get('type')
    cname = control['name']

    if columns == 1:
        row_y = y + item_index * CONTROL_HEIGHT
        if ctype == 'DXSoundBar': label_align, control_align = 250, 70
        elif ctype == 'DXCheckBox': label_align, control_align = 280, 100
        elif ctype == 'DXButton':
            return (
                f"new Point(({SECTION_WIDTH} - {cname}.Size.Width) / 2, {row_y})",
                f"new Point({SECTION_WIDTH} - {{LABEL}}.Size.Width, {row_y})",
            )
        else: label_align, control_align = 230, 100
        return (
            f"new Point({SECTION_WIDTH} - {control_align} - {cname}.Size.Width, {row_y})",
            f"new Point({SECTION_WIDTH} - {label_align} - {{LABEL}}.Size.Width, {row_y})",
        )

    row = item_index // 2
    is_left = item_index % 2 == 0
    row_y = y + row * CONTROL_HEIGHT
    column_offset = 175 if is_left else 0
    label_align = section.get('_twoColumnLabelAlign', 175)
    if ctype == 'DXColourControl' or control.get('sourceType') == 'DXColourControlPair':
        label_align = 70
        section['_twoColumnLabelAlign'] = 70
    control_align = 25
    return (
        f"new Point({SECTION_WIDTH} - {control_align} - {column_offset} - {cname}.Size.Width, {row_y})",
        f"new Point({SECTION_WIDTH} - {label_align} - {column_offset} - {{LABEL}}.Size.Width, {row_y})",
    )


def apply(spec: dict, zircon_root: Path) -> dict:
    window = next((w for w in spec.get('windows', []) if w.get('field') == 'ConfigBox'), None)
    if not window or not window.get('sourcePath'):
        return {'sections': 0, 'controlsPlaced': 0, 'labelsAdded': 0, 'artAdded': 0}

    source = (zircon_root / window['sourcePath']).read_text(encoding='utf-8-sig')
    body = constructor_body(source, window['class'])
    sections = parse_sections(body)
    calls = scan_calls(body, sections)
    finish_section_geometry(sections, calls)
    import_report = ensure_section_controls(window, sections, source)

    controls_by_name = {c.get('name'): c for c in window.get('controls', [])}
    additions: list[dict] = []
    placed = labels = 0
    pair_children = 0
    section_report = []

    for section in sections.values():
        if not section['tab']: continue
        section.pop('_twoColumnLabelAlign', None)
        additions.extend(add_section_artwork(section))
        for i, row in enumerate(section['controls']):
            control = controls_by_name.get(row['control'])
            if not control: continue
            control_location, label_location = placement(section, control, i)
            props = control.setdefault('properties', {})
            if 'Location' in props: control.setdefault('sourcePreConfigSectionLocation', props['Location'])
            if 'Parent' in props: control.setdefault('sourcePreConfigSectionParent', props['Parent'])
            props['Parent'] = section['tab']
            props['Location'] = control_location
            control['configSection'] = section['name']
            control['configSectionLayoutSource'] = 'DXConfigSection.UpdateControlLocations'
            placed += 1

            if control.get('sourceType') == 'DXColourControlPair':
                children = synthetic_colour_pair_children(control, section['tab'])
                additions.extend(children)
                pair_children += len(children)

            if not is_blank_label(row['label']):
                label_name = f"ConfigSection__{section['name']}__Label__{i + 1}"
                additions.append(synthetic_label(
                    label_name, section['tab'], row['label'],
                    label_location.replace('{LABEL}', label_name),
                ))
                labels += 1

        section_report.append({
            'name': section['name'], 'tab': section['tab'], 'columns': section['columns'],
            'controls': len(section['controls']), 'rows': section['rows'],
            'y': section['sectionY'], 'height': section['height'],
        })

    window['controls'].extend(additions)
    refs = spec.setdefault('assetRefs', {})
    gameinter = {int(v) for v in refs.get('GameInter', [])}
    gameinter.update({4750, 4751, 4752})
    refs['GameInter'] = sorted(gameinter)

    report = {
        'sourceBacked': True,
        'algorithm': 'DXConfigTab.AddSection + DXConfigSection.UpdateControlLocations',
        'sections': len(section_report),
        'controlsRequested': sum(len(s['controls']) for s in sections.values()),
        'controlsPlaced': placed,
        'targetTypedControlsImported': len(import_report['imported']),
        'targetTypedImportedNames': [c['name'] for c in import_report['imported']],
        'unresolvedSectionControls': import_report['unresolved'],
        'colourPairChildrenAdded': pair_children,
        'labelsAdded': labels,
        'syntheticSectionVisualControlsAdded': len(additions) - labels - pair_children,
        'sectionWidth': SECTION_WIDTH,
        'headerHeight': HEADER_HEIGHT,
        'controlHeight': CONTROL_HEIGHT,
        'footerHeight': FOOTER_HEIGHT,
        'sectionDetails': section_report,
        'runtimeComboItemsInvented': False,
    }
    window['configSectionLayout'] = report
    spec['configSectionPass'] = report
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    report = apply(spec, args.zircon_root)
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Config sections:', report['sections'])
    print('Config controls requested:', report.get('controlsRequested'))
    print('Config controls placed:', report['controlsPlaced'])
    print('Target-typed Config controls imported:', report.get('targetTypedControlsImported'))
    print('Unresolved Config section controls:', report.get('unresolvedSectionControls'))
    print('Config colour-pair children added:', report.get('colourPairChildrenAdded'))
    print('Config labels added:', report['labelsAdded'])
    print('Config section visual controls added:', report['syntheticSectionVisualControlsAdded'])


if __name__ == '__main__':
    main()
