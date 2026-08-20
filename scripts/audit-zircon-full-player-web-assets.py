#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ATLAS_SCHEMA = "origins.zircon.web-atlas.v1"
CONTRACT_SCHEMA = "origins.zircon.web-player-assets.v1"
BODY_RE = re.compile(r"^(?:M|WM)_Hum")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_child(root: Path, relative: str) -> Path:
    root = root.resolve()
    child = (root / relative).resolve()
    if child != root and root not in child.parents:
        raise ValueError(f"Path escapes root {root}: {relative}")
    return child


def category(name: str) -> str:
    if BODY_RE.match(name):
        return "body"
    if name.startswith(("M_Hair", "WM_Hair")):
        return "hair"
    if name.startswith(("M_Costume", "WM_Costume")):
        return "costume"
    if name.startswith("Horse"):
        return "horse"
    if name.startswith(("M_Shield", "WM_Shield")):
        return "shield"
    if name.startswith(("M_Weapon", "WM_Weapon")):
        return "weapon"
    if name.startswith(("M_Helmet", "WM_Helmet")):
        return "helmet"
    return "other"


def audit_library(asset_root: Path, entry: dict, expected_source: dict, atlas_size: int) -> dict:
    name = entry.get("libraryFile")
    manifest_rel = entry.get("manifest")
    if not isinstance(name, str) or not name:
        raise ValueError("Master entry missing libraryFile")
    if not isinstance(manifest_rel, str) or not manifest_rel:
        raise ValueError(f"{name}: master entry missing manifest")

    manifest_path = safe_child(asset_root, manifest_rel)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"{name}: missing manifest {manifest_path}")
    manifest = load_json(manifest_path)
    if manifest.get("schema") != ATLAS_SCHEMA:
        raise ValueError(f"{name}: manifest schema mismatch: {manifest.get('schema')!r}")
    if manifest.get("libraryFile") != name:
        raise ValueError(f"{name}: manifest libraryFile mismatch")
    if manifest.get("sourcePath") != expected_source.get("sourcePath"):
        raise ValueError(f"{name}: sourcePath mismatch")
    if int(manifest.get("atlasSize", -1)) != atlas_size:
        raise ValueError(f"{name}: atlas size mismatch")

    image_count = int(manifest.get("imageCount", -1))
    exported = int(manifest.get("exportedImageCount", -1))
    images = manifest.get("images")
    pages = manifest.get("pages")
    if image_count <= 0:
        raise ValueError(f"{name}: imageCount must be positive")
    if exported <= 0:
        raise ValueError(f"{name}: no exported images")
    if not isinstance(images, list) or len(images) != image_count:
        raise ValueError(f"{name}: images array length does not match imageCount")
    if not isinstance(pages, list) or not pages:
        raise ValueError(f"{name}: no atlas pages")

    page_paths: dict[str, Path] = {}
    page_bytes = 0
    for page in pages:
        if not isinstance(page, str) or not page:
            raise ValueError(f"{name}: invalid page entry")
        if page in page_paths:
            raise ValueError(f"{name}: duplicate page {page}")
        page_path = safe_child(manifest_path.parent, page)
        if not page_path.is_file() or page_path.stat().st_size <= 0:
            raise FileNotFoundError(f"{name}: missing/empty atlas page {page}")
        page_paths[page] = page_path
        page_bytes += page_path.stat().st_size

    non_null = 0
    for position, image in enumerate(images):
        if image is None:
            continue
        non_null += 1
        if int(image.get("index", -1)) != position:
            raise ValueError(f"{name}: image index mismatch at slot {position}")
        page = image.get("page")
        if page not in page_paths:
            raise ValueError(f"{name}: frame {position} refers to unknown page {page!r}")
        x = int(image.get("x", -1))
        y = int(image.get("y", -1))
        width = int(image.get("width", 0))
        height = int(image.get("height", 0))
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise ValueError(f"{name}: invalid geometry for frame {position}")
        if x + width > atlas_size or y + height > atlas_size:
            raise ValueError(f"{name}: frame {position} exceeds atlas bounds")
        if not isinstance(image.get("offsetX"), int) or not isinstance(image.get("offsetY"), int):
            raise ValueError(f"{name}: frame {position} offsets are not integers")

    if non_null != exported:
        raise ValueError(f"{name}: exportedImageCount={exported}, non-null records={non_null}")

    source_sha = manifest.get("sourceSha256")
    if not isinstance(source_sha, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", source_sha):
        raise ValueError(f"{name}: invalid source SHA-256")

    return {
        "libraryFile": name,
        "category": category(name),
        "imageCount": image_count,
        "exportedImageCount": exported,
        "emptyImageSlots": image_count - exported,
        "pageCount": len(pages),
        "atlasBytes": page_bytes,
        "sourceSha256": source_sha.upper(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed audit for the complete pinned-Zircon PlayerObject web asset export.")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fishing-probe", type=Path)
    args = parser.parse_args()

    contract = load_json(args.contract)
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise SystemExit(f"Unexpected contract schema: {contract.get('schema')!r}")

    asset_root = args.asset_root.resolve()
    master_path = asset_root / "player-assets.json"
    if not master_path.is_file():
        raise SystemExit(f"Missing full player master manifest: {master_path}")
    master = load_json(master_path)
    if master.get("schema") != ATLAS_SCHEMA:
        raise SystemExit(f"Unexpected master schema: {master.get('schema')!r}")
    if master.get("zirconCommit") != contract.get("zirconCommit"):
        raise SystemExit("Zircon commit mismatch between source contract and exported payload")

    required_rows = contract.get("playerLibraries")
    if not isinstance(required_rows, list) or not required_rows:
        raise SystemExit("Contract playerLibraries missing")
    expected = {row["libraryFile"]: row for row in required_rows}
    entries = master.get("libraries")
    if not isinstance(entries, list):
        raise SystemExit("Master libraries must be an array")
    actual = {entry.get("libraryFile"): entry for entry in entries}
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise SystemExit(f"Full player library set mismatch. missing={missing}, extra={extra}")

    atlas_size = int(master.get("atlasSize", -1))
    if atlas_size <= 0:
        raise SystemExit("Invalid master atlas size")

    library_rows = [audit_library(asset_root, actual[name], expected[name], atlas_size) for name in sorted(expected, key=str.casefold)]

    selectors = contract.get("playerLibrarySelectors") or {}
    selector_values = []
    selector_counts = {}
    for selector_name in ("ArmourList", "CostumeList", "WeaponList", "ShieldList", "HelmetList"):
        mapping = selectors.get(selector_name)
        if not isinstance(mapping, dict):
            raise SystemExit(f"Missing selector map: {selector_name}")
        selector_counts[selector_name] = len(mapping)
        selector_values.extend(mapping.values())
    selector_missing = sorted(set(selector_values) - set(actual))
    if selector_missing:
        raise SystemExit(f"Selector libraries missing from exported payload: {selector_missing}")

    auxiliary_required = {
        "M_Hair", "WM_Hair", "M_HairA", "WM_HairA",
        "Horse", "HorseIron", "HorseSilver", "HorseGold", "HorseBlue",
        "HorseDark", "HorseDarkEffect", "HorseRoyal", "HorseRoyalEffect",
        "HorseBlueDragon", "HorseBlueDragonEffect",
    }
    auxiliary_missing = sorted(auxiliary_required - set(actual))
    if auxiliary_missing:
        raise SystemExit(f"Runtime auxiliary player libraries missing: {auxiliary_missing}")

    player_frames = contract.get("playerFrames") or {}
    if len(player_frames) != 42:
        raise SystemExit(f"Expected 42 FrameSet.Players definitions, got {len(player_frames)}")
    magic_map = contract.get("magicAnimationMap") or {}
    if len(magic_map) < 100:
        raise SystemExit(f"Unexpectedly small magic animation map: {len(magic_map)}")
    selector_total = sum(selector_counts.values())
    if selector_total != 122:
        raise SystemExit(f"Expected 122 PlayerObject selector entries, got {selector_total}")

    category_counts = Counter(row["category"] for row in library_rows)
    if category_counts.get("other", 0):
        raise SystemExit(f"Unclassified player libraries remain: {category_counts['other']}")

    fishing = None
    if args.fishing_probe and args.fishing_probe.is_file():
        probe = load_json(args.fishing_probe)
        female_full = int(probe.get("FemaleFullFishingBanks", 0))
        male_full = int(probe.get("MaleFullFishingBanks", 0))
        fishing = {
            "probeStatus": probe.get("Status"),
            "maleFullFishingBanks": male_full,
            "femaleFullFishingBanks": female_full,
            "payloadStatus": "COMPLETE_OFFICIAL_BANK_FOUND" if female_full > 0 else "UPSTREAM_FEMALE_FISHING_GAP",
        }
        if probe.get("Status") != "PASS":
            raise SystemExit(f"Fishing probe pipeline did not pass: {probe.get('Status')}")

    total_png_bytes = sum(row["atlasBytes"] for row in library_rows)
    total_images = sum(row["imageCount"] for row in library_rows)
    total_exported = sum(row["exportedImageCount"] for row in library_rows)

    report = {
        "schema": "origins.zircon.full-player-web-assets-audit.v1",
        "status": "PASS",
        "zirconCommit": contract.get("zirconCommit"),
        "libraryCount": len(library_rows),
        "expectedLibraryCount": len(required_rows),
        "categoryCounts": dict(sorted(category_counts.items())),
        "selectorCounts": selector_counts,
        "selectorCount": selector_total,
        "playerAnimationCount": len(player_frames),
        "magicAnimationMappingCount": len(magic_map),
        "totalImageSlots": total_images,
        "totalExportedImages": total_exported,
        "totalEmptyImageSlots": total_images - total_exported,
        "totalAtlasPngBytes": total_png_bytes,
        "fishing": fishing,
        "libraries": library_rows,
        "boundary": {
            "allPlayerLibrariesExported": True,
            "allPlayerObjectSelectorsResolvable": True,
            "nativeOffsetsPreserved": True,
            "crystalFallbackAllowed": False,
            "upstreamEmptySlotsAreNotFabricated": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "libraryCount": report["libraryCount"],
        "selectorCount": report["selectorCount"],
        "playerAnimationCount": report["playerAnimationCount"],
        "totalExportedImages": report["totalExportedImages"],
        "totalAtlasPngBytes": report["totalAtlasPngBytes"],
        "fishing": fishing,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
