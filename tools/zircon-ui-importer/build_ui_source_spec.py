#!/usr/bin/env python3
"""Build a machine-readable specification of Zircon's complete in-game UI.

The source of truth is the current Suprcode/Zircon C# client. This script does
not attempt to translate the game client; it inventories GameScene windows and
extracts declarative geometry/art references useful to the ORIGINS HTML
reference renderer.

C# expressions are kept as strings when they cannot be reduced safely. That is
preferable to silently inventing a coordinate or image index.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

GAME_SCENE_FIELDS = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)")
LIB_FILE = re.compile(r"LibraryFile\.([A-Za-z_][A-Za-z0-9_]*)")
INTEGER = re.compile(r"(?<![A-Za-z_])\d+(?![A-Za-z_])")

ROOT_PROPS = {
    "LibraryFile", "Index", "Size", "Location", "Visible", "Movable", "Sort",
    "DropShadow", "Opacity", "HasTitle", "HasFooter", "HasTopBorder", "SlimFooter",
    "AllowResize", "CanResizeWidth", "CanResizeHeight", "PassThrough",
}


def match_brace(text: str, opening: int) -> int:
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
            if c == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if c == "*" and n == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_char:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == "'":
                in_char = False
            i += 1
            continue
        if in_string:
            if verbatim:
                if c == '"':
                    if n == '"':
                        i += 2
                        continue
                    in_string = False
                    verbatim = False
            else:
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == '"':
                    in_string = False
            i += 1
            continue
        if c == "/" and n == "/":
            line_comment = True
            i += 2
            continue
        if c == "/" and n == "*":
            block_comment = True
            i += 2
            continue
        if c == '@' and n == '"':
            in_string = True
            verbatim = True
            i += 2
            continue
        if c == '"':
            in_string = True
            i += 1
            continue
        if c == "'":
            in_char = True
            i += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced braces")


def constructor_body(text: str, class_name: str) -> str:
    m = re.search(
        rf"\bpublic\s+{re.escape(class_name)}\s*\([^)]*\)\s*(?::\s*[^{{]+)?\{{",
        text,
    )
    if not m:
        return ""
    opening = text.find("{", m.start())
    return text[opening + 1:match_brace(text, opening)]


def named_method_body(text: str, method_name: str) -> str:
    m = re.search(rf"\b{re.escape(method_name)}\s*\([^)]*\)\s*\{{", text)
    if not m:
        return ""
    opening = text.find("{", m.start())
    return text[opening + 1:match_brace(text, opening)]


def split_top_level(text: str, delimiter: str) -> list[str]:
    """Split on a delimiter only when outside nested C# syntax.

    This is deliberately a small lexical scanner rather than a C# parser. It
    preserves commas inside Point/Size constructors, method calls, nested
    object initializers, lambdas, arrays, strings, chars and comments.
    """
    out: list[str] = []
    start = 0
    braces = 0
    parens = 0
    brackets = 0
    in_string = False
    verbatim = False
    in_char = False
    escaped = False
    line_comment = False
    block_comment = False
    i = 0
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if c == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if c == "*" and n == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_char:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == "'":
                in_char = False
            i += 1
            continue
        if in_string:
            if verbatim:
                if c == '"':
                    if n == '"':
                        i += 2
                        continue
                    in_string = False
                    verbatim = False
            else:
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == '"':
                    in_string = False
            i += 1
            continue
        if c == "/" and n == "/":
            line_comment = True
            i += 2
            continue
        if c == "/" and n == "*":
            block_comment = True
            i += 2
            continue
        if c == '@' and n == '"':
            in_string = True
            verbatim = True
            i += 2
            continue
        if c == '"':
            in_string = True
            i += 1
            continue
        if c == "'":
            in_char = True
            i += 1
            continue
        if c == '{':
            braces += 1
        elif c == '}':
            braces = max(0, braces - 1)
        elif c == '(':
            parens += 1
        elif c == ')':
            parens = max(0, parens - 1)
        elif c == '[':
            brackets += 1
        elif c == ']':
            brackets = max(0, brackets - 1)
        elif c == delimiter and braces == 0 and parens == 0 and brackets == 0:
            out.append(text[start:i])
            start = i + 1
        i += 1
    out.append(text[start:])
    return out


def top_level_statements(body: str) -> list[str]:
    return [part.strip() for part in split_top_level(body, ';') if part.strip()]


def strip_leading_comments(statement: str) -> str:
    value = statement.lstrip()
    while value:
        if value.startswith("//"):
            pos = value.find("\n")
            if pos < 0:
                return ""
            value = value[pos + 1:].lstrip()
            continue
        if value.startswith("/*"):
            pos = value.find("*/", 2)
            if pos < 0:
                return ""
            value = value[pos + 2:].lstrip()
            continue
        break
    return value


def simple_assignments(body: str, allowed: set[str] | None = None) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in top_level_statements(body):
        statement = strip_leading_comments(raw)
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)\s*$", statement, re.S)
        if m:
            key, value = m.group(1), " ".join(m.group(2).split())
            if allowed is None or key in allowed:
                out[key] = value
        m = re.match(r"\s*SetClientSize\s*\(\s*new\s+Size\s*\((.*)\)\s*\)\s*$", statement, re.S)
        if m:
            out["ClientSize"] = f"new Size({' '.join(m.group(1).split())})"
    return out


def object_initializers(body: str) -> list[dict]:
    controls: list[dict] = []
    pat = re.compile(
        r"(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*)"
        r"new\s+(DX[A-Za-z_][A-Za-z0-9_]*)\s*\{"
    )
    for m in pat.finditer(body):
        opening = body.find("{", m.start())
        try:
            closing = match_brace(body, opening)
        except ValueError:
            continue
        chunk = body[opening + 1:closing]
        props: dict[str, str] = {}
        for entry in split_top_level(chunk, ','):
            mm = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$", entry, re.S)
            if mm:
                props[mm.group(1)] = " ".join(mm.group(2).split())
        controls.append({"name": m.group(1), "type": m.group(2), "properties": props})

    # Enrich only from constructor-level assignments. Event-handler changes are
    # later runtime states and must not overwrite the initial visual state.
    by_name = {c["name"]: c for c in controls}
    for raw in top_level_statements(body):
        statement = strip_leading_comments(raw)
        m = re.match(
            r"\s*([A-Za-z_][A-Za-z0-9_]*)\.(Location|Size|Index|Visible|LibraryFile|Opacity|ButtonType|Checked)\s*=\s*(.+)\s*$",
            statement,
            re.S,
        )
        if not m:
            continue
        name, prop, value = m.group(1), m.group(2), " ".join(m.group(3).split())
        if name in by_name:
            by_name[name]["properties"][prop] = value
    return controls


def literal_indices(expr: str | None) -> list[int]:
    if not expr:
        return []
    return sorted({int(x) for x in INTEGER.findall(expr)})


def find_source(source_root: Path, class_name: str, cache: dict[str, tuple[Path | None, str]]) -> tuple[Path | None, str]:
    if class_name in cache:
        return cache[class_name]
    for path in source_root.rglob("*.cs"):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        if re.search(rf"\bclass\s+{re.escape(class_name)}\b", text):
            cache[class_name] = (path, text)
            return path, text
    cache[class_name] = (None, "")
    return None, ""


def parse_library_map(zircon_root: Path) -> dict[str, str]:
    text = (zircon_root / "LibraryCore" / "Libraries.cs").read_text(encoding="utf-8-sig")
    return {
        enum: value.replace("\\", "/")
        for enum, value in re.findall(
            r"\[LibraryFile\.([A-Za-z0-9_]+)\]\s*=\s*@\"([^\"]+\.Zl)\"",
            text,
        )
    }


def game_scene_registry(zircon_root: Path) -> list[dict]:
    text = (zircon_root / "Client" / "Scenes" / "GameScene.cs").read_text(encoding="utf-8-sig")
    ctor = constructor_body(text, "GameScene")
    if not ctor:
        raise RuntimeError("Unable to locate Zircon GameScene constructor body")

    items: list[dict] = [{"field": "MainPanel", "class": "MainPanel", "defaultVisible": True}]
    seen = {"MainPanel"}
    for m in GAME_SCENE_FIELDS.finditer(ctor):
        field, cls = m.group(1), m.group(2)
        if field in seen or field in {"MapControl"}:
            continue
        if not (field.endswith("Box") or field in {"ChatTextBox", "BeltBox", "MiniMapBox", "BuffBox", "TimerBox"}):
            continue
        tail = ctor[m.end():m.end() + 300]
        vm = re.search(r"Visible\s*=\s*(true|false)", tail)
        visible = (vm.group(1) == "true") if vm else True
        items.append({"field": field, "class": cls, "defaultVisible": visible})
        seen.add(field)

    defaults = named_method_body(text, "SetDefaultLocations")
    locs: dict[str, str] = {}
    for raw in top_level_statements(defaults):
        statement = strip_leading_comments(raw)
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\.Location\s*=\s*(.+)\s*$", statement, re.S)
        if m:
            locs[m.group(1)] = " ".join(m.group(2).split())
    for item in items:
        if item["field"] in locs:
            item["defaultLocationExpression"] = locs[item["field"]]
    return items


def build_spec(zircon_root: Path) -> dict:
    libraries = parse_library_map(zircon_root)
    registry = game_scene_registry(zircon_root)
    source_root = zircon_root / "Client"
    cache: dict[str, tuple[Path | None, str]] = {}
    asset_refs: dict[str, set[int]] = {"Interface": set(range(0, 27)) | {126}}

    for item in registry:
        path, text = find_source(source_root, item["class"], cache)
        if not path:
            item.update({"sourcePath": None, "baseClass": None, "root": {}, "controls": [], "sourceMissing": True})
            continue
        decl = re.search(rf"\bclass\s+{re.escape(item['class'])}\s*:\s*([^\n\{{]+)", text)
        base_class = decl.group(1).strip() if decl else None
        body = constructor_body(text, item["class"])
        root = simple_assignments(body, ROOT_PROPS)
        controls = object_initializers(body)
        item.update({
            "sourcePath": path.relative_to(zircon_root).as_posix(),
            "baseClass": base_class,
            "root": root,
            "controls": controls,
            "sourceMissing": False,
        })

        root_libs = LIB_FILE.findall(root.get("LibraryFile", ""))
        root_indices = literal_indices(root.get("Index"))
        for lib in root_libs:
            asset_refs.setdefault(lib, set()).update(root_indices)

        for control in controls:
            p = control["properties"]
            libs = LIB_FILE.findall(p.get("LibraryFile", ""))
            ids = literal_indices(p.get("Index"))
            for lib in libs:
                asset_refs.setdefault(lib, set()).update(ids)

        control_lib = {}
        for control in controls:
            libs = LIB_FILE.findall(control["properties"].get("LibraryFile", ""))
            if libs:
                control_lib[control["name"]] = libs[0]
        for raw in top_level_statements(body):
            statement = strip_leading_comments(raw)
            m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\.Index\s*=\s*(.+)\s*$", statement, re.S)
            if not m:
                continue
            lib = control_lib.get(m.group(1))
            if lib:
                asset_refs.setdefault(lib, set()).update(literal_indices(m.group(2)))

    # Stable common ranges/reference-only icons used by the desktop harness.
    asset_refs.setdefault("GameInter", set()).update(range(50, 130))
    asset_refs["GameInter"].update({161, 162, 240, 241, 358, 360, 364, 960, 1298})
    asset_refs.setdefault("Interface", set()).update(range(0, 320))
    asset_refs.setdefault("MagicIcon", set()).update({0, 8, 10, 14, 18, 20, 30, 38, 40, 44, 52, 64})

    return {
        "sourceRepository": "https://github.com/Suprcode/Zircon",
        "sourceBranch": "master",
        "scope": "Complete Zircon in-game GameScene UI",
        "windowCount": len(registry),
        "libraries": libraries,
        "assetRefs": {k: sorted(v) for k, v in sorted(asset_refs.items()) if v},
        "windows": registry,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--zircon-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    spec = build_spec(args.zircon_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(f"Zircon UI spec: {spec['windowCount']} GameScene entries -> {args.out}")
    for lib, ids in spec["assetRefs"].items():
        print(f"  {lib}: {len(ids)} referenced/required IDs")


if __name__ == "__main__":
    main()
