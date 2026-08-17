#!/usr/bin/env python3
"""Bundle the validated viewer patch and modular source-fidelity runtimes.

This final assembly pass also promotes DXWindow inherited-child constructor
assignments (CloseButton/TitleLabel) into the generated source manifest. They
are real source state, but are not normal object initializers in derived C#
constructors, so the base inventory cannot otherwise expose them to the viewer.
"""
from __future__ import annotations

import json
import re
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
runpy.run_path(str(here / "patch_multiwindow_runtime_core.py"), run_name="__main__")

if len(sys.argv) < 2:
    raise SystemExit("Expected generated app-layout.js path")

build_root = Path(sys.argv[1]).resolve().parent
repo_root = here.parents[1]
index_path = build_root / "index.html"
spec_path = build_root / "ui-source-spec.json"
if not index_path.exists() or not spec_path.exists():
    raise SystemExit("Generated Zircon viewer/spec missing")


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    in_string = False
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
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == '"': in_string = False
            i += 1; continue
        if c == "/" and n == "/": line_comment = True; i += 2; continue
        if c == "/" and n == "*": block_comment = True; i += 2; continue
        if c == '"': in_string = True; i += 1; continue
        if c == "'": in_char = True; i += 1; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    raise ValueError("unbalanced C# constructor braces")


def constructor_body(text: str, class_name: str) -> str:
    match = re.search(rf"\bpublic\s+{re.escape(class_name)}\s*\([^)]*\)\s*(?::\s*[^{{]+)?\{{", text)
    if not match: return ""
    opening = text.find("{", match.start())
    return text[opening + 1:matching_brace(text, opening)]


def augment_inherited_window_chrome() -> None:
    zircon_root = repo_root / ".source" / "Zircon"
    if not zircon_root.exists():
        print("Zircon checkout unavailable for inherited DXWindow chrome pass")
        return
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    changed = 0
    keys = {
        ("CloseButton", "Visible"): "CloseButtonVisible",
        ("CloseButton", "Enabled"): "CloseButtonEnabled",
        ("TitleLabel", "Visible"): "TitleLabelVisible",
    }
    for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = item.get("sourcePath")
        class_name = item.get("class") or item.get("sourceClass")
        if not source_path or not class_name: continue
        path = zircon_root / source_path
        if not path.exists(): continue
        text = path.read_text(encoding="utf-8-sig")
        body = constructor_body(text, class_name)
        if not body: continue
        root = item.setdefault("root", {})
        for (child, prop), output_key in keys.items():
            matches = list(re.finditer(rf"\b{child}\s*\.\s*{prop}\s*=\s*(true|false)\s*;", body, re.I))
            if not matches: continue
            value = matches[-1].group(1).lower()
            if root.get(output_key) != value:
                root[output_key] = value
                changed += 1
    by_field = {item.get("field"): item for item in spec.get("windows", [])}
    expected = {
        "BeltBox": ("false", "false"),
        "MiniMapBox": ("false", None),
        "BuffBox": ("false", "false"),
    }
    for field, (close_visible, title_visible) in expected.items():
        root = (by_field.get(field) or {}).get("root", {})
        if root.get("CloseButtonVisible") != close_visible:
            raise SystemExit(f"Inherited CloseButton.Visible extraction failed for {field}: {root}")
        if title_visible is not None and root.get("TitleLabelVisible") != title_visible:
            raise SystemExit(f"Inherited TitleLabel.Visible extraction failed for {field}: {root}")
    spec.setdefault("inheritedWindowChromePass", {})["assignmentsPromoted"] = changed
    spec["inheritedWindowChromePass"]["source"] = "derived constructor CloseButton/TitleLabel assignments"
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Inherited DXWindow chrome assignments promoted:", changed)


augment_inherited_window_chrome()

visual = repo_root / "apps" / "zircon-ui-reference" / "visual-control-runtime.js"
entries: list[tuple[Path, Path]] = [(visual, Path("visual-control-runtime.js"))]
extra_dir = repo_root / "apps" / "zircon-ui-reference" / "extra-runtimes"
if extra_dir.exists():
    entries += [(source, Path("extra-runtimes") / source.name) for source in sorted(extra_dir.glob("*.js"))]

index = index_path.read_text(encoding="utf-8")
anchor = '  <script type="module" src="animated-control-runtime.js"></script>\n'
if anchor not in index:
    raise SystemExit("Animated runtime script anchor missing")

for source, relative in entries:
    if not source.exists(): raise SystemExit(f"Fidelity runtime missing: {source}")
    target = build_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    subprocess.run(["node", "--check", str(target)], check=True)
    index = index.replace(f'  <script type="module" src="{relative.as_posix()}"></script>\n', "")

block = anchor + "".join(f'  <script type="module" src="{relative.as_posix()}"></script>\n' for _, relative in entries)
index = index.replace(anchor, block, 1)
index_path.write_text(index, encoding="utf-8")

animated = build_root / "animated-control-runtime.js"
if not animated.exists(): raise SystemExit(f"Bundled runtime missing: {animated}")
subprocess.run(["node", "--check", str(animated)], check=True)
print("Bundled fidelity runtimes:", ", ".join(relative.as_posix() for _, relative in entries))