#!/usr/bin/env python3
"""Bundled ORIGINS HispaCrystal analyzer adapter.

This adapter makes `origins_hpr_zircon_builder.py analyze` self-contained.
It delegates raw HPR parsing to the verified real-v3 reader already bundled in
this folder (`origins_hpr_zircon_v2.py`) and exports the exact artifacts the
master builder expects: CURSOR_PROFILE.json, IMAGE_METADATA.csv and FRAMES_PNG.

Accepted CLI forms (for compatibility with the wrapper):
    python monster_hpr_analyzer.py INPUT OUTPUT
    python monster_hpr_analyzer.py --input INPUT --output OUTPUT
    python monster_hpr_analyzer.py --input-dir INPUT --output-dir OUTPUT
    python monster_hpr_analyzer.py --source INPUT --output OUTPUT
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _parse_args() -> tuple[Path, Path]:
    p = argparse.ArgumentParser(description="ORIGINS bundled HispaCrystal HPR analyzer")
    p.add_argument("input_pos", nargs="?")
    p.add_argument("output_pos", nargs="?")
    p.add_argument("--input", dest="input_flag")
    p.add_argument("--output", dest="output_flag")
    p.add_argument("--input-dir", dest="input_dir")
    p.add_argument("--output-dir", dest="output_dir")
    p.add_argument("--source", dest="source")
    ns = p.parse_args()

    source = ns.input_flag or ns.input_dir or ns.source or ns.input_pos
    output = ns.output_flag or ns.output_dir or ns.output_pos
    if not source or not output:
        p.error("input and output are required")
    return Path(source).resolve(), Path(output).resolve()


def main() -> int:
    source, output = _parse_args()
    tool_root = Path(__file__).resolve().parent.parent
    engine = tool_root / "origins_hpr_zircon_v2.py"
    if not engine.exists():
        raise SystemExit(f"Bundled real-v3 reader missing: {engine}")

    output.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(engine),
        "batch",
        str(source),
        "--out",
        str(output),
        "--no-zl",
        "--export-png",
        "--fail-exit-code",
    ]
    proc = subprocess.run(cmd)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
