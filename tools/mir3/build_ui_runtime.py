#!/usr/bin/env python3
"""Extract the small ORIGINS X login/character UI runtime from MIR3 ZL libraries.

Example:
    python tools/mir3/build_ui_runtime.py \
        --interface1c "Data/Interface1c.Zl" \
        --extended "Data/Interface1c-Extended.Zl" \
        --gameinter "Data/GameInter.Zl" \
        --out assets/ui

Only the frames used by the current web flow are exported.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from build_map_runtime import LegacyZlLibrary

CHARACTER_FRAMES = {
    "warrior-male": 300,
    "warrior-female": 500,
    "wizard-male": 800,
    "wizard-female": 1000,
    "taoist-male": 1300,
    "taoist-female": 1500,
    "assassin-male": 1800,
    "assassin-female": 2000,
}


def save_webp(image: Image.Image, path: Path, *, quality: int = 82, max_size=None):
    image = image.convert("RGBA")
    if max_size:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "WEBP", quality=quality, method=6)


def decode_required(library: LegacyZlLibrary, index: int, label: str) -> Image.Image:
    image = library.decode(index)
    if image is None:
        raise ValueError(f"Missing {label} frame {index} in {library.path.name}")
    return image


def build(args):
    out = args.out.resolve()
    interface1c = LegacyZlLibrary(args.interface1c.resolve())
    extended = LegacyZlLibrary(args.extended.resolve())
    gameinter = LegacyZlLibrary(args.gameinter.resolve())

    save_webp(
        decode_required(extended, 0, "login background"),
        out / "login" / "login-bg.webp",
        quality=78,
        max_size=(1280, 720),
    )
    save_webp(
        decode_required(extended, 2, "selection background"),
        out / "login" / "select-bg.webp",
        quality=78,
        max_size=(1280, 720),
    )
    save_webp(
        decode_required(interface1c, 22, "logo"),
        out / "login" / "logo.webp",
        quality=88,
        max_size=(564, 300),
    )

    for name, index in CHARACTER_FRAMES.items():
        save_webp(
            decode_required(interface1c, index, name),
            out / "characters" / f"{name}.webp",
            quality=88,
            max_size=(320, 520),
        )

    save_webp(
        decode_required(gameinter, 116, "config button"),
        out / "controls" / "config-116.webp",
        quality=92,
    )

    print(f"Built ORIGINS X UI runtime in {out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface1c", type=Path, required=True)
    parser.add_argument("--extended", type=Path, required=True)
    parser.add_argument("--gameinter", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("assets/ui"))
    build(parser.parse_args())


if __name__ == "__main__":
    main()
