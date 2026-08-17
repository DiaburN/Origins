#!/usr/bin/env python3
"""Bundle the validated viewer patch and modular source-fidelity runtimes."""
from __future__ import annotations

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
if not index_path.exists():
    raise SystemExit(f"Generated index missing: {index_path}")

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
    if not source.exists():
        raise SystemExit(f"Fidelity runtime missing: {source}")
    target = build_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    subprocess.run(["node", "--check", str(target)], check=True)
    tag = f'  <script type="module" src="{relative.as_posix()}"></script>\n'
    index = index.replace(tag, "")

block = anchor + "".join(
    f'  <script type="module" src="{relative.as_posix()}"></script>\n'
    for _, relative in entries
)
index = index.replace(anchor, block, 1)
index_path.write_text(index, encoding="utf-8")

animated = build_root / "animated-control-runtime.js"
if not animated.exists():
    raise SystemExit(f"Bundled runtime missing: {animated}")
subprocess.run(["node", "--check", str(animated)], check=True)
print("Bundled fidelity runtimes:", ", ".join(relative.as_posix() for _, relative in entries))