#!/usr/bin/env python3
"""Build the exact Zircon MainPanel/GameInter runtime used by the browser UI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_full_zircon_ui import ZLLibrary, find_library, pack, save_lossless

# Exact GameInter indexes used by Zircon Client/Scenes/Views/MainPanel.cs
# plus the MiniMap controls that sit in the same in-game UI layer.
# GameInter[0] is intentionally omitted because it is blank in the supplied library.
MAIN_PANEL_INDICES = [
    50, 51, 52, 54, 56, 58, 59,
    62, 63, 64, 65, 66, 70, 71, 72, 73,
    82, 87, 92, 97, 102, 107, 112, 117, 122,
    130, 131, 132, 137,
    240, 241,
]


def build(repo: Path, source: Path | None):
    gameinter_path = find_library(repo, source, ["GameInter.Zl", "GameInter(1).Zl"])
    print(f"GameInter: {gameinter_path}")

    library = ZLLibrary(gameinter_path)
    items = [(f"gameinter-{index}", library.decode(index)) for index in MAIN_PANEL_INDICES]

    out_dir = repo / "assets" / "ui" / "zircon"
    sheet_path = out_dir / "gameinter-mainpanel.webp"
    placements = pack(items, sheet_path, 2048)

    sprites = {
        name: {"x": x, "y": y, "w": width, "h": height}
        for name, (x, y, width, height) in placements.items()
    }
    runtime = {
        "sheet": "assets/ui/zircon/gameinter-mainpanel.webp",
        "sprites": sprites,
        "design": {"width": 1024, "height": 768, "panelWidth": 1024, "panelHeight": 68},
    }

    js_path = repo / "js" / "ui" / "mainpanel-assets.js"
    js_path.parent.mkdir(parents=True, exist_ok=True)
    js_path.write_text(
        "window.G = window.G || {};\n\nG.MainPanelAssets = Object.freeze(" +
        json.dumps(runtime, separators=(",", ":")) +
        ");\n",
        encoding="utf-8",
    )

    # Keep the standalone background in sync with the exact source library.
    save_lossless(library.decode(50), out_dir / "main-panel.webp")

    print("Generated exact Zircon MainPanel runtime:")
    print(f"  {sheet_path.relative_to(repo)} ({sheet_path.stat().st_size:,} bytes)")
    print("  js/ui/mainpanel-assets.js")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Directory containing GameInter.Zl")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2], help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        build(args.repo.resolve(), args.source)
    except FileNotFoundError as exc:
        print("Could not find GameInter.Zl:")
        print(f"  {exc}")
        print("Run again with --source pointing to the folder that contains GameInter.Zl.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
