#!/usr/bin/env python3
"""Build CharacterDialog paperdoll runtime from original ProgUse.Zl.

Zircon CharacterDialog does not use the world player sprite or a class preview.
It draws a base body from ProgUse and then overlays hair/equipment/effects at
one shared origin. This builder exports the verified base/hair source frames
with their original offsets. Equip layers will be exported on demand once
actual equipment image indices are known.

Missing ProgUse.Zl is NOT fatal: the browser must simply leave the paperdoll
empty instead of inventing replacement art.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_full_zircon_ui import ZLLibrary, find_library, pack

# CharacterDialog.cs verified ranges. Standard hair uses 60/80 bases and
# Assassin hair uses 1100/1120 bases, implying 20 slots per family.
PROGUSE_INDICES = [0, 1, *range(60, 100), *range(1100, 1140), 1160]


def build(repo: Path, source: Path | None) -> bool:
    try:
        path = find_library(repo, source, ["ProgUse.Zl", "ProgUse(1).Zl"])
    except FileNotFoundError:
        print("ProgUse.Zl not found; Character paperdoll remains intentionally empty.")
        return False

    print(f"ProgUse: {path}")
    library = ZLLibrary(path)
    items = []
    metadata = {}

    for index in PROGUSE_INDICES:
        if index < 0 or index >= len(library.images) or library.images[index] is None:
            continue
        image = library.decode(index)
        meta = library.images[index]
        name = f"proguse-{index}"
        items.append((name, image))
        metadata[str(index)] = {
            "name": name,
            "w": image.width,
            "h": image.height,
            "ox": int(meta.ox),
            "oy": int(meta.oy),
        }

    if not items:
        print("ProgUse.Zl was found but none of the verified Character frames exist.")
        return False

    out_dir = repo / "assets" / "ui" / "zircon" / "paperdoll"
    atlas_path = out_dir / "proguse.webp"
    placements = pack(items, atlas_path, 2048)

    for index, item in metadata.items():
        x, y, w, h = placements[item["name"]]
        item.update({"x": x, "y": y, "w": w, "h": h})
        item.pop("name", None)

    runtime = {
        "ready": True,
        "sheet": "assets/ui/zircon/paperdoll/proguse.webp",
        "source": "ProgUse.Zl",
        "origin": [130, 270],
        "frames": metadata,
        "baseBody": {"male": 0, "female": 1},
        "hair": {
            "standardMaleBase": 60,
            "standardFemaleBase": 80,
            "assassinMaleBase": 1100,
            "assassinFemaleBase": 1120,
            "assassinFemaleSpecial": 1160,
        },
        "equipmentReady": False,
    }

    js_path = repo / "js" / "ui" / "character-paperdoll-assets.js"
    js_path.write_text(
        "window.G = window.G || {};\n\nG.CharacterPaperdollAssets = Object.freeze(" +
        json.dumps(runtime, separators=(",", ":")) +
        ");\n",
        encoding="utf-8",
    )

    print("Generated CharacterDialog ProgUse runtime:")
    print(f"  {atlas_path.relative_to(repo)} ({atlas_path.stat().st_size:,} bytes)")
    print("  js/ui/character-paperdoll-assets.js")
    return True


def write_empty(repo: Path):
    js_path = repo / "js" / "ui" / "character-paperdoll-assets.js"
    js_path.parent.mkdir(parents=True, exist_ok=True)
    js_path.write_text(
        "window.G = window.G || {};\n\nG.CharacterPaperdollAssets = Object.freeze({ready:false,frames:{}});\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Directory containing ProgUse.Zl")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2], help=argparse.SUPPRESS)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not build(repo, args.source):
        write_empty(repo)


if __name__ == "__main__":
    main()
