#!/usr/bin/env python3
"""Run the established viewer patcher, then bundle modular visual-fidelity runtimes.

Keeping this wrapper tiny lets the source-faithful viewer grow in independent,
node-checked modules without rewriting the proven multi-window patcher.
"""
from __future__ import annotations

import runpy
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE / "patch_multiwindow_runtime_core.py"

# Preserve the original command line: the core parser still owns the app-layout
# argument and performs every established patch exactly as before.
runpy.run_path(str(CORE), run_name="__main__")

if len(sys.argv) < 2:
    raise SystemExit("Expected generated app-layout.js path")

app_layout = Path(sys.argv[1]).resolve()
build_root = app_layout.parent
repo_root = HERE.parents[1]
visual_source = repo_root / "apps" / "zircon-ui-reference" / "visual-control-runtime.js"
visual_target = build_root / "visual-control-runtime.js"
animated_target = build_root / "animated-control-runtime.js"
index_path = build_root / "index.html"

if not visual_source.exists():
    raise SystemExit(f"Visual fidelity runtime missing: {visual_source}")
if not index_path.exists():
    raise SystemExit(f"Generated index missing: {index_path}")

shutil.copyfile(visual_source, visual_target)

index = index_path.read_text(encoding="utf-8")
script = '  <script type="module" src="visual-control-runtime.js"></script>\n'
if script not in index:
    animated = '  <script type="module" src="animated-control-runtime.js"></script>\n'
    if animated in index:
        index = index.replace(animated, animated + script, 1)
    elif "</body>" in index:
        index = index.replace("</body>", script + "</body>", 1)
    else:
        raise SystemExit("Could not place visual fidelity runtime in generated index")
    index_path.write_text(index, encoding="utf-8")

# These modules are part of the official artifact; syntax failure must fail CI.
for runtime in (animated_target, visual_target):
    if not runtime.exists():
        raise SystemExit(f"Bundled runtime missing: {runtime}")
    subprocess.run(["node", "--check", str(runtime)], check=True)

print("Bundled and node-checked animated-control-runtime.js")
print("Bundled and node-checked visual-control-runtime.js")