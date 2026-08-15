#!/usr/bin/env python3
"""ORIGINS public-source bootstrap.

Downloads the exact external source material currently needed by the ORIGINS
vertical slice into .source/ and runs the repository importers into artifacts/.
No previous ChatGPT-uploaded archive is used.

Usage:
    python3 scripts/bootstrap_sources.py --all
    python3 scripts/bootstrap_sources.py --zuma
    python3 scripts/bootstrap_sources.py --player
    python3 scripts/bootstrap_sources.py --zircon
"""

from __future__ import annotations

import argparse
import gzip
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".source"
ARTIFACTS = ROOT / "artifacts"
UA = "Mozilla/5.0 (ORIGINS source bootstrap)"


def download(urls: list[str], target: Path, gz: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        print(f"[keep] {target.relative_to(ROOT)}")
        return

    last_error: Exception | None = None
    for url in urls:
        print(f"[get] {url}")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                payload = response.read()
            if gz:
                payload = gzip.decompress(payload)
            target.write_bytes(payload)
            if target.stat().st_size <= 0:
                raise RuntimeError("download produced an empty file")
            print(f"[ok]  {target.relative_to(ROOT)} ({target.stat().st_size:,} bytes)")
            return
        except Exception as exc:  # try public fallback mirror/path
            last_error = exc
            print(f"[retry] {exc}")

    raise RuntimeError(f"Unable to download {target}: {last_error}")


def run(*args: str) -> None:
    cmd = [sys.executable if args[0].endswith(".py") else args[0], *args[1:]]
    print("[run]", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def bootstrap_zuma() -> None:
    print("\n=== ZUMA / MIR2 ===")
    maps = SOURCE / "maps"
    data = SOURCE / "WemadeMir2"

    download([
        "https://raw.githubusercontent.com/Suprcode/Crystal.Database/main/Jev/Maps/d501.map"
    ], maps / "d501.map")
    download([
        "https://raw.githubusercontent.com/Suprcode/Crystal.Database/main/Jev/Maps/d515.map"
    ], maps / "d515.map")

    base = "https://files.lomcn.co.uk/resources/mir2/crystal/patch_oldversion/Data/Map/WeMade-Mir2"
    for remote, local in [
        ("Tiles.Lib.gz", "Tiles.Lib"),
        ("SmTiles.Lib.gz", "SmTiles.Lib"),
        ("Objects2.Lib.gz", "Objects2.Lib"),
        ("Objects6.Lib.gz", "Objects6.Lib"),
    ]:
        download([f"{base}/{remote}"], data / local, gz=True)

    out = ARTIFACTS / "zuma"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    run(
        "tools/crystal-map-importer/extract_theme_assets_complete.py",
        "--data", str(data),
        "--maps", str(maps),
        "--standard", "d501.map",
        "--king", "d515.map",
        "--theme", "zuma_gray",
        "--out", str(out),
    )

    ref = out / "reference"
    ref.mkdir(parents=True, exist_ok=True)
    run(
        "tools/crystal-map-importer/render_mir2_2010_reference.py",
        "--data", str(data),
        "--map", str(maps / "d515.map"),
        "--out", str(ref / "d515-full.png"),
    )
    run(
        "tools/crystal-map-importer/export_mir2_2010_placements.py",
        "--data", str(data),
        "--map", str(maps / "d515.map"),
        "--out", str(ref / "d515-placements.json"),
    )


def bootstrap_player() -> None:
    print("\n=== CRYSTAL PLAYER LOCOMOTION ===")
    lib = SOURCE / "CArmour" / "00.Lib"
    download([
        "https://files.lomcn.co.uk/resources/mir2/crystal/patch/Data/CArmour/00.Lib.gz",
        "https://files.lomcn.co.uk/resources/mir2/crystal/patch_oldversion/Data/CArmour/00.Lib.gz",
    ], lib, gz=True)

    out = ARTIFACTS / "player-locomotion"
    if out.exists():
        shutil.rmtree(out)
    run(
        "tools/crystal-character-importer/extract_player_locomotion.py",
        "--lib", str(lib),
        "--out", str(out),
    )


def bootstrap_zircon() -> None:
    print("\n=== ZIRCON UI ===")
    data = SOURCE / "zircon"
    base = "https://files.lomcn.co.uk/resources/mir3/zircon/patch"
    names = [
        "GameInter.Zl", "GameInter2.Zl", "Interface.Zl", "Equip.Zl",
        "Inventory.Zl", "MIcon.Zl", "QuestIcons.Zl", "MiniMapIcon.Zl", "CBIcons.Zl",
    ]
    for name in names:
        remote = f"Data-{name}.gz"
        download([f"{base}/{remote}"], data / name, gz=True)

    ref = ARTIFACTS / "zircon-ui-reference"
    if ref.exists():
        shutil.rmtree(ref)
    (ref / "assets" / "GameInter").mkdir(parents=True, exist_ok=True)
    (ref / "assets" / "Interface").mkdir(parents=True, exist_ok=True)
    (ref / "assets" / "MIcon").mkdir(parents=True, exist_ok=True)

    run(
        "tools/zircon-ui-importer/extract_zl_assets.py",
        str(data / "GameInter.Zl"), str(ref / "assets" / "GameInter"),
        "--ids", "0-300,350-370,960-970,1290-1310,6580-6610",
    )
    run(
        "tools/zircon-ui-importer/extract_zl_assets.py",
        str(data / "Interface.Zl"), str(ref / "assets" / "Interface"),
        "--ids", "0-310",
    )
    run(
        "tools/zircon-ui-importer/extract_zl_assets.py",
        str(data / "MIcon.Zl"), str(ref / "assets" / "MIcon"),
        "--ids", "0-200",
    )

    for name in ("index.html", "styles.css", "app.js"):
        shutil.copy2(ROOT / "apps" / "zircon-ui-reference" / name, ref / name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--zuma", action="store_true")
    parser.add_argument("--player", action="store_true")
    parser.add_argument("--zircon", action="store_true")
    args = parser.parse_args()

    if not any((args.all, args.zuma, args.player, args.zircon)):
        parser.error("select --all, --zuma, --player or --zircon")

    SOURCE.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    if args.all or args.zuma:
        bootstrap_zuma()
    if args.all or args.player:
        bootstrap_player()
    if args.all or args.zircon:
        bootstrap_zircon()

    print("\nORIGINS source bootstrap complete.")
    print(f"Source cache: {SOURCE}")
    print(f"Generated artifacts: {ARTIFACTS}")


if __name__ == "__main__":
    main()
