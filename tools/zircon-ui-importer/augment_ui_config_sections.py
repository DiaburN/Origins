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

Only controls already present in the manifest are repositioned. No runtime combo
items, monitor modes or other live data are invented.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from build_ui_source_spec import constructor_body, match_brace, split_top_level, top_level_statements, strip_leading_comments

SECTION_RE = re.compile(r"\bDXConfigSection\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s*\((.*?)\)\s*\{", re.S)
ADD_CONTROL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.AddControl\s*\((.*)\)$", re.S)
ADD_SECTION_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.AddSection\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)$", re.S)
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

SECTION_WIDTH = 348
HEADER_HEIGHT = 25
CONTROL_HEIGHT = 20
FOOTER_HEIGHT = 5


def normalise(value: str) -> str:
    return " ".join(value.strip().split())


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
        try:
            columns = int(columns_raw)
        except ValueError:
            columns = 1
        result[name] = {
            'name': name,
            'title': normalise(title),
            'columns': max(1, columns),
            'declaredParent': props.get('Parent'),
            'controls': [],
            'tab': None,
            'sectionY': 0,
        }
    return result


def parse_calls(body: str, sections: dict[str, dict]) -> None:
    add_section_order: list[tuple[str, str]] = []
    for raw in top_level_statements(body):
        statement = strip_leading_comments(raw)
        control_match = ADD_CONTROL_RE.match(statement)
        if control_match:
            section_name, args_text = control_match.groups()
            section = sections.get(section_name)
            if not section:
                continue
            args = split_top_level(args_text, ',')
            if len(args) != 2:
                continue
            label_expr = normalise(args[0])
            control_expr = normalise(args[1])
            if IDENT_RE.fullmatch(control_expr):
                section['controls'].append({'label': label_expr, 'control': control_expr})
            continue

        section_match = ADD_SECTION_RE.match(statement)
        if section_match:
            tab, section_name = section_match.groups()
            if section_name in sections:
                add_section_order.append((tab, section_name))

    heights: dict[str, int] = {}
    for name, section in sections.items():
        rows = math.ceil(len(section['controls']) / section['columns']) if section['controls'] else 0
        heights[name] = HEADER_HEIGHT + rows * CONTROL_HEIGHT + FOOTER_HEIGHT
        section['rows'] = rows
        section['height'] = heights[name]

    cursor_by_tab: dict[str, int] = {}
    for tab, section_name in add_section_order:
        section = sections[section_name]
        y = cursor_by_tab.get(tab, 0)
        section['tab'] = tab
        section['sectionY'] = y
        cursor_by_tab[tab] = y + heights[section_name]


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


def is_blank_label(expression: str) -> bool:
    value = expression.strip()
    return value in {'""', 'string.Empty', 'String.Empty'}


def add_section_artwork(section: dict) -> list[dict]:
    tab = section['tab']
    if not tab:
        return []
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
        if i == 0:
            location = f"new Point(0, {y} + {header_name}.Size.Height)"
        else:
            location = f"new Point(0, {y} + {header_name}.Size.Height + {i} * {body0_name}.Size.Height)"
        out.append(synthetic_image(name, tab, 4751, location))
    footer_name = f"{prefix}__Footer"
    if body_count:
        footer_location = f"new Point(0, {y} + {header_name}.Size.Height + {body_count} * {body0_name}.Size.Height)"
    else:
        footer_location = f"new Point(0, {y} + {header_name}.Size.Height)"
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
        if ctype == 'DXSoundBar':
            label_align, control_align = 250, 70
        elif ctype == 'DXCheckBox':
            label_align, control_align = 280, 100
        elif ctype == 'DXButton':
            label_align = 0
            return (
                f"new Point(({SECTION_WIDTH} - {cname}.Size.Width) / 2, {row_y})",
                f"new Point({SECTION_WIDTH} - {label_align} - {{LABEL}}.Size.Width, {row_y})",
            )
        else:
            label_align, control_align = 230, 100
        return (
            f"new Point({SECTION_WIDTH} - {control_align} - {cname}.Size.Width, {row_y})",
            f"new Point({SECTION_WIDTH} - {label_align} - {{LABEL}}.Size.Width, {row_y})",
        )

    row = item_index // 2
    is_left = item_index % 2 == 0
    row_y = y + row * CONTROL_HEIGHT
    column_offset = 175 if is_left else 0
    # DXConfigSection keeps this variable at 70 after a colour control occurs.
    # The caller supplies the correct effective value via section state.
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
    parse_calls(body, sections)

    controls_by_name = {c.get('name'): c for c in window.get('controls', [])}
    additions: list[dict] = []
    placed = labels = 0
    section_report = []

    for section in sections.values():
        if not section['tab']:
            continue
        section.pop('_twoColumnLabelAlign', None)
        art = add_section_artwork(section)
        additions.extend(art)
        for i, row in enumerate(section['controls']):
            control = controls_by_name.get(row['control'])
            if not control:
                continue
            control_location, label_location = placement(section, control, i)
            props = control.setdefault('properties', {})
            if 'Location' in props:
                control.setdefault('sourcePreConfigSectionLocation', props['Location'])
            if 'Parent' in props:
                control.setdefault('sourcePreConfigSectionParent', props['Parent'])
            props['Parent'] = section['tab']
            props['Location'] = control_location
            control['configSection'] = section['name']
            control['configSectionLayoutSource'] = 'DXConfigSection.UpdateControlLocations'
            placed += 1

            if not is_blank_label(row['label']):
                label_name = f"ConfigSection__{section['name']}__Label__{i + 1}"
                label_location = label_location.replace('{LABEL}', label_name)
                additions.append(synthetic_label(label_name, section['tab'], row['label'], label_location))
                labels += 1

        section_report.append({
            'name': section['name'],
            'tab': section['tab'],
            'columns': section['columns'],
            'controls': len(section['controls']),
            'rows': section['rows'],
            'y': section['sectionY'],
            'height': section['height'],
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
        'controlsPlaced': placed,
        'labelsAdded': labels,
        'syntheticSectionVisualControlsAdded': len(additions) - labels,
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
    print('Config controls placed:', report['controlsPlaced'])
    print('Config labels added:', report['labelsAdded'])
    print('Config section visual controls added:', report['syntheticSectionVisualControlsAdded'])


if __name__ == '__main__':
    main()
