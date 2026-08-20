#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE_HUMANS = ("M_Hum", "WM_Hum")
DIRECTIONS = tuple(range(8))
PLAYER_BODY_SHAPE_OFFSET = 5000
PLAYER_BODY_SHAPES_PER_LIBRARY = tuple(range(11))
FISHING_ANIMATIONS = ("FishingCast", "FishingWait", "FishingReel")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def local_frames_used_by_pinned_runtime(animation: str, frame_count: int) -> tuple[int, ...]:
    # Client/Models/MapObject.UpdateFrame in pinned Zircon forces Player + Pushed to frame = 0
    # after reversed-frame interpolation. Therefore only local frame zero is ever drawn for players.
    if animation == "Pushed":
        return (0,)
    return tuple(range(frame_count))


def frame_present(images: list, image_index: int) -> bool:
    return 0 <= image_index < len(images) and images[image_index] is not None


def scan_animation(images: list, *, start: int, offset: int, local_frames: tuple[int, ...], shape_shift: int = 0) -> tuple[int, list[dict]]:
    missing: list[dict] = []
    references = 0
    for direction in DIRECTIONS:
        for local_frame in local_frames:
            image_index = shape_shift + start + offset * direction + local_frame
            references += 1
            if not frame_present(images, image_index):
                missing.append({
                    "direction": direction,
                    "localFrame": local_frame,
                    "imageIndex": image_index,
                })
    return references, missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit real Zircon base-human atlas coverage using pinned PlayerObject/MapObject draw semantics.")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--asset-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    contract_path = Path(args.contract)
    asset_root = Path(args.asset_root)
    output_path = Path(args.output)

    contract = load_json(contract_path)
    frames = contract.get("playerFrames")
    if not isinstance(frames, dict) or not frames:
        raise SystemExit("Contract has no playerFrames.")

    master = load_json(asset_root / "player-assets.json")
    libraries = {row["libraryFile"]: row for row in master.get("libraries", [])}
    if set(libraries) != set(BASE_HUMANS):
        raise SystemExit(f"Expected exactly {set(BASE_HUMANS)}, got {set(libraries)}")

    manifests: dict[str, dict] = {}
    for library in BASE_HUMANS:
        manifest_path = asset_root / libraries[library]["manifest"]
        manifest = load_json(manifest_path)
        if manifest.get("libraryFile") != library:
            raise SystemExit(f"Manifest/library mismatch for {library}")
        if not isinstance(manifest.get("images"), list):
            raise SystemExit(f"{library}: manifest has no indexed images array")
        manifests[library] = manifest

    missing: list[dict] = []
    animation_rows: list[dict] = []
    total_references = 0

    for animation, definition in frames.items():
        start = int(definition["startIndex"])
        count = int(definition["frameCount"])
        offset = int(definition["offset"])
        local_frames = local_frames_used_by_pinned_runtime(animation, count)
        animation_missing = 0
        animation_references = 0

        for library in BASE_HUMANS:
            images = manifests[library]["images"]
            references, rows = scan_animation(images, start=start, offset=offset, local_frames=local_frames)
            animation_references += references
            total_references += references
            animation_missing += len(rows)
            for row in rows:
                missing.append({"libraryFile": library, "animation": animation, **row})

        animation_rows.append({
            "animation": animation,
            "frameCount": count,
            "runtimeLocalFrameCount": len(local_frames),
            "runtimeLocalFrames": list(local_frames),
            "directionCount": len(DIRECTIONS),
            "libraryCount": len(BASE_HUMANS),
            "references": animation_references,
            "missing": animation_missing,
            "status": "PASS" if animation_missing == 0 else "FAIL",
            "runtimeSpecialCase": "Player Pushed forces local frame 0" if animation == "Pushed" else None,
        })

    # Fishing is stored in the same player body libraries and ArmourFrame adds
    # (ArmourShape % 11) * 5000 for Warrior/Wizard/Taoist. Probe all eleven internal
    # body-shape banks so we can distinguish a true importer problem from empty source banks.
    fishing_shape_coverage: list[dict] = []
    for library in BASE_HUMANS:
        images = manifests[library]["images"]
        for shape in PLAYER_BODY_SHAPES_PER_LIBRARY:
            shift = shape * PLAYER_BODY_SHAPE_OFFSET
            shape_missing = 0
            shape_references = 0
            animation_details = []
            for animation in FISHING_ANIMATIONS:
                definition = frames[animation]
                start = int(definition["startIndex"])
                count = int(definition["frameCount"])
                offset = int(definition["offset"])
                local_frames = tuple(range(count))
                references, rows = scan_animation(images, start=start, offset=offset, local_frames=local_frames, shape_shift=shift)
                shape_references += references
                shape_missing += len(rows)
                animation_details.append({
                    "animation": animation,
                    "references": references,
                    "missing": len(rows),
                    "status": "PASS" if not rows else "FAIL",
                })
            fishing_shape_coverage.append({
                "libraryFile": library,
                "armourShapeModulo11": shape,
                "shapeShift": shift,
                "references": shape_references,
                "missing": shape_missing,
                "status": "PASS" if shape_missing == 0 else ("PARTIAL" if shape_missing < shape_references else "EMPTY"),
                "animations": animation_details,
            })

    result = {
        "schema": "origins.zircon.base-human-animation-coverage.v2",
        "status": "PASS" if not missing else "FAIL",
        "zirconCommit": contract.get("zirconCommit"),
        "libraries": list(BASE_HUMANS),
        "animationCount": len(frames),
        "directionCount": len(DIRECTIONS),
        "totalFrameReferences": total_references,
        "missingFrameReferences": len(missing),
        "runtimeSemantics": {
            "pushedPlayerLocalFrames": [0],
            "pushedSource": "Client/Models/MapObject.cs UpdateFrame: Player + MirAction.Pushed forces frame = 0",
            "fishingBodySource": "Client/Models/PlayerObject.cs DrawBody: BodyLibrary.GetImage(ArmourFrame)",
            "bodyShapeOffset": PLAYER_BODY_SHAPE_OFFSET,
            "bodyShapeBankCount": len(PLAYER_BODY_SHAPES_PER_LIBRARY),
        },
        "animations": animation_rows,
        "fishingShapeCoverage": fishing_shape_coverage,
        "missing": missing,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "animationCount": result["animationCount"],
        "totalFrameReferences": result["totalFrameReferences"],
        "missingFrameReferences": result["missingFrameReferences"],
        "fishingShapePasses": [
            f"{row['libraryFile']}:{row['armourShapeModulo11']}"
            for row in fishing_shape_coverage if row["status"] == "PASS"
        ],
    }, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
