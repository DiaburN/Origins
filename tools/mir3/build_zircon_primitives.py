#!/usr/bin/env python3
"""Build exact browser UI primitive assets from Zircon Interface.Zl.

The browser uses these raw source parts to reproduce DXWindow, DXButton,
DXTab, DXItemCell decorations and scroll controls. No artwork is redrawn.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_full_zircon_ui import ZLLibrary, find_library, pack

# Exact Interface.Zl parts referenced by DXWindow / DXButton / common controls
# plus CharacterDialog's empty equipment-slot artwork.
INTERFACE_INDICES = [
    *range(0, 13),
    15,
    16, 17, 18, 19,
    25, 26,
    31, 32, 33, 34, 36, 38, 39, 40,
    41, 42, 43,
    # DXItemCell state overlays: New / Locked / CannotUse.
    47, 48, 49,
    53, 54, 55, 56, 57, 58,
    60, 61, 62, 65,
    81, 82,
    # DXItemCell ItemPart marker + Character Emblem placeholder.
    103, 104,
    126,
    241, 242, 243, 245,
]


def build(repo: Path, source: Path | None):
    interface_path = find_library(repo, source, ["Interface.Zl", "Interface(1).Zl"])
    print(f"Interface: {interface_path}")
    library = ZLLibrary(interface_path)

    out_dir = repo / "assets" / "ui" / "zircon"
    atlas_path = out_dir / "ui-primitives.webp"
    placements = pack(
        [(f"interface-{index}", library.decode(index)) for index in INTERFACE_INDICES],
        atlas_path,
        1024,
    )

    sprites = {
        name: {"x": x, "y": y, "w": width, "h": height}
        for name, (x, y, width, height) in placements.items()
    }

    # Values are asset-derived, matching DXControl/DXWindow static constructors.
    size = lambda index: [library.decode(index).width, library.decode(index).height]
    runtime = {
        "sheet": "assets/ui/zircon/ui-primitives.webp",
        "sprites": sprites,
        "metrics": {
            "defaultHeight": size(16)[1],
            "tabHeight": size(19)[1],
            "smallButtonHeight": size(41)[1],
            "headerBarSize": size(0)[1],
            "headerSize": size(0)[1] + size(3)[1],
            "noHeaderSize": size(2)[1],
            "footerSize": size(126)[1] + size(2)[1] + size(10)[1],
            "noFooterSize": size(2)[1],
            "slimFooterSize": size(126)[1],
        },
    }

    js_path = repo / "js" / "ui" / "zircon-primitives-assets.js"
    js_path.write_text(
        "window.G = window.G || {};\n\nG.ZirconPrimitiveAssets = Object.freeze(" +
        json.dumps(runtime, separators=(",", ":")) +
        ");\n",
        encoding="utf-8",
    )

    print("Generated Zircon UI primitives:")
    print(f"  {atlas_path.relative_to(repo)} ({atlas_path.stat().st_size:,} bytes)")
    print("  js/ui/zircon-primitives-assets.js")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Directory containing Interface.Zl")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2], help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        build(args.repo.resolve(), args.source)
    except FileNotFoundError as exc:
        print("Could not find Interface.Zl:")
        print(f"  {exc}")
        print("Run again with --source pointing to the folder that contains Interface.Zl.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
