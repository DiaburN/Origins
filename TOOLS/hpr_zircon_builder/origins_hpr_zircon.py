#!/usr/bin/env python3
"""ORIGINS HPR -> Zircon Monster Builder.

Goals
-----
* Read HispaCrystal .hpr monster libraries without renumbering source image IDs.
* Recover every image's dimensions/offsets/shadow metadata and RGBA pixels.
* Reuse previously verified CURSOR_PROFILE / ALL_MONSTERS_CURSOR_MANIFEST data
  when available instead of guessing animation semantics.
* Write a Zircon ZL2 library using PNG payloads while preserving slot indexes.
* Emit exact per-action/per-direction source index maps, Cursor instructions and
  a batch MASTER_SHEET (CSV/JSON/HTML).

The tool deliberately keeps VISUAL animation separate from SERVER behaviour.
Attack*, Range*, Spell*, Special* labels are visual slots only unless an explicit
semantic override says otherwise.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import io
import json
import os
import shutil
import struct
import sys
import tempfile
import traceback
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit("Pillow is required. Run: py -m pip install -r requirements.txt") from exc

SIGNATURE = b"HispaCrystal"
HPR_DIRECTION_NAMES = [
    "Up", "UpRight", "Right", "DownRight", "Down", "DownLeft", "Left", "UpLeft"
]
# Confirmed project convention from the previous HPR analysis work.
MIR2_TO_ZIRCON_DIRECTION_SHIFT = 3

# ZL2 values mirrored by TOOLS/zl_extractor/zl_extract.py in this repository.
ZL2_VERSION = 2
ZL_CODEC_PNG = 4
ZL_COMPRESSION_NONE = 0
ZL_ENTRY_IMAGE = 0
ZL_RUNTIME_SOURCE = 6

SAFE_STRUCTURAL = {
    "Standing": "Standing",
    "Walking": "Moving",
    "Running": "Moving",
    "Pushed": "Moving",
    "Struck": "Struck",
    "Die": "Die",
    "Dead": "Dead",
    "Skeleton": "Skeleton",
    "Revive": "Revive",
    "Show": "Show",
    "Hide": "Hide",
}


class HprError(RuntimeError):
    pass


class ZlError(RuntimeError):
    pass


@dataclass(frozen=True)
class HprRecordLayout:
    name: str
    fmt: str
    has_mask: bool
    pad_before_length: int = 0

    @property
    def size(self) -> int:
        return struct.calcsize(self.fmt)


# Hispa libraries seen in this project use compact records.  We probe all known
# variants and only accept a layout when every record parses through EOF and all
# non-empty gzip payloads decompress to width*height*4 BGRA bytes.
HPR_RECORD_LAYOUTS = [
    HprRecordLayout("u16_xy_shadow_mask", "<HHhhhhBBI", True),
    HprRecordLayout("u16_xy_shadow", "<HHhhhhBI", False),
    HprRecordLayout("i16_xy_shadow_mask", "<hhhhhhBBI", True),
    HprRecordLayout("u16_xy_shadow_mask_align2", "<HHhhhhBBxxI", True, 2),
]


@dataclass
class HprImage:
    index: int
    present: bool
    width: int = 0
    height: int = 0
    x: int = 0
    y: int = 0
    shadow_x: int = 0
    shadow_y: int = 0
    shadow_type: int = 0
    mask: int = 0
    compressed_length: int = 0
    record_offset: int = 0
    payload_offset: int = 0
    rgba: Optional[bytes] = field(default=None, repr=False)

    def png_bytes(self) -> bytes:
        if not self.present or self.rgba is None:
            raise HprError(f"image {self.index}: no pixel payload")
        image = Image.frombytes("RGBA", (self.width, self.height), self.rgba)
        out = io.BytesIO()
        image.save(out, "PNG", optimize=False, compress_level=9)
        return out.getvalue()


@dataclass
class ActionProfile:
    visual_action: str
    zircon_animation_slot: str
    start: int
    count: int
    stride: int
    delay_ms: int
    reverse: bool = False
    semantic: str = "UNKNOWN_VISUAL_ONLY"
    semantic_source: str = "not-inferred"
    holley_name: str = ""
    action_id: Optional[int] = None
    effect_start: Optional[int] = None
    effect_count: Optional[int] = None
    effect_stride: Optional[int] = None
    effect_delay_ms: Optional[int] = None


@dataclass
class MonsterProfile:
    hpr: str
    status: str = "REVIEW_FRAMESET_UNKNOWN"
    slot_count: int = 0
    nonempty_image_count: int = 0
    actions: List[ActionProfile] = field(default_factory=list)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    unreferenced_nonempty_ranges: List[Dict[str, int]] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    source: str = "raw-hpr"


@dataclass
class ParsedHpr:
    path: Path
    hpr_id: str
    version: Optional[int]
    version_encoding: str
    image_table_offset: int
    image_record_layout: str
    images: List[HprImage]
    profile: MonsterProfile
    source_sha256: str


@dataclass
class BuildResult:
    hpr: str
    source_file: str
    source_sha256: str
    hpr_version: Optional[int]
    image_layout: str
    slot_count: int
    present_count: int
    status: str
    profile_source: str
    action_count: int
    actions: str
    unknown_behavior_actions: str
    unreferenced_graphics: int
    zl_file: str
    output_folder: str
    issues: str
    warnings: str


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def natural_key(text: str) -> Tuple[Any, ...]:
    parts: List[Any] = []
    token = ""
    numeric = False
    for ch in text:
        if ch.isdigit() == numeric:
            token += ch
        else:
            if token:
                parts.append(int(token) if numeric else token.lower())
            token = ch
            numeric = ch.isdigit()
    if token:
        parts.append(int(token) if numeric else token.lower())
    return tuple(parts)


def hpr_id_from_path(path: Path) -> str:
    stem = path.stem
    if stem.lower().endswith(".hpr"):
        stem = Path(stem).stem
    return stem


def int_value(obj: Dict[str, Any], *keys: str, default: int = 0) -> int:
    for key in keys:
        if key in obj and obj[key] is not None:
            return int(obj[key])
    return default


def bool_value(obj: Dict[str, Any], *keys: str, default: bool = False) -> bool:
    for key in keys:
        if key in obj and obj[key] is not None:
            value = obj[key]
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "y", "si", "sí"}
            return bool(value)
    return default


def str_value(obj: Dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        if key in obj and obj[key] is not None:
            return str(obj[key])
    return default


def contiguous_ranges(values: Iterable[int]) -> List[Dict[str, int]]:
    seq = sorted(set(values))
    if not seq:
        return []
    out: List[Dict[str, int]] = []
    start = prev = seq[0]
    for value in seq[1:]:
        if value != prev + 1:
            out.append({"start": start, "end": prev, "count": prev - start + 1})
            start = value
        prev = value
    out.append({"start": start, "end": prev, "count": prev - start + 1})
    return out


# ---------------------------------------------------------------------------
# Previously verified analysis/profile loader
# ---------------------------------------------------------------------------

def normalize_action(raw: Dict[str, Any], combat_index: int) -> ActionProfile:
    visual = str_value(raw, "visual_action", "action", "name", default=f"Action{combat_index}")
    zircon = str_value(raw, "zircon_animation_slot", "mir_animation", "slot")
    if not zircon:
        if visual in SAFE_STRUCTURAL:
            zircon = visual
        else:
            zircon = f"Combat{combat_index}"
    semantic = str_value(raw, "semantic")
    semantic_source = str_value(raw, "semantic_source")
    if not semantic:
        semantic = SAFE_STRUCTURAL.get(visual, "UNKNOWN_VISUAL_ONLY")
    if not semantic_source:
        semantic_source = "safe-structural" if visual in SAFE_STRUCTURAL else "not-inferred"
    count = int_value(raw, "frame_count", "count")
    stride = int_value(raw, "direction_stride", "stride")
    if not stride:
        skip = int_value(raw, "skip")
        stride = count + skip
    return ActionProfile(
        visual_action=visual,
        zircon_animation_slot=zircon,
        start=int_value(raw, "start_index", "start"),
        count=count,
        stride=stride,
        delay_ms=int_value(raw, "delay_ms", "delay", default=100),
        reverse=bool_value(raw, "reversed", "reverse"),
        semantic=semantic,
        semantic_source=semantic_source,
        holley_name=str_value(raw, "holley_name"),
        action_id=(int(raw["action_id"]) if raw.get("action_id") is not None else None),
        effect_start=(int_value(raw, "effect_start_index", "effect_start") if any(k in raw for k in ("effect_start_index", "effect_start")) else None),
        effect_count=(int_value(raw, "effect_frame_count", "effect_count") if any(k in raw for k in ("effect_frame_count", "effect_count")) else None),
        effect_stride=(int_value(raw, "effect_direction_stride", "effect_stride") if any(k in raw for k in ("effect_direction_stride", "effect_stride")) else None),
        effect_delay_ms=(int_value(raw, "effect_delay_ms", "effect_delay") if any(k in raw for k in ("effect_delay_ms", "effect_delay")) else None),
    )


def normalize_profile(hpr_id: str, raw: Dict[str, Any], source: str) -> MonsterProfile:
    actions: List[ActionProfile] = []
    combat = 1
    for action_raw in raw.get("actions", raw.get("animations", [])) or []:
        action = normalize_action(action_raw, combat)
        actions.append(action)
        if action.zircon_animation_slot.lower().startswith("combat") or action.visual_action not in SAFE_STRUCTURAL:
            combat += 1
    return MonsterProfile(
        hpr=str(raw.get("hpr", raw.get("id", hpr_id))),
        status=str(raw.get("status", "AUTO_PROFILE" if actions else "REVIEW_FRAMESET_UNKNOWN")),
        slot_count=int(raw.get("slot_count", raw.get("slots", 0)) or 0),
        nonempty_image_count=int(raw.get("nonempty_image_count", raw.get("sprites", 0)) or 0),
        actions=actions,
        effects=list(raw.get("effects", []) or []),
        unreferenced_nonempty_ranges=list(raw.get("unreferenced_nonempty_ranges", []) or []),
        issues=[str(x) for x in (raw.get("issues", []) or [])],
        warnings=[str(x) for x in (raw.get("warnings", []) or [])],
        source=source,
    )


def load_manifest(path: Optional[Path]) -> Dict[str, MonsterProfile]:
    if not path:
        return {}
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(obj, dict):
        # Allow {"monsters": [...]} and {"1829": {...}} forms.
        if isinstance(obj.get("monsters"), list):
            rows = obj["monsters"]
        else:
            rows = []
            for key, value in obj.items():
                if isinstance(value, dict):
                    value = dict(value)
                    value.setdefault("hpr", key)
                    rows.append(value)
    elif isinstance(obj, list):
        rows = obj
    else:
        raise ValueError(f"Unsupported manifest JSON root: {type(obj).__name__}")
    out: Dict[str, MonsterProfile] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        hid = str(raw.get("hpr", raw.get("id", ""))).strip()
        if not hid:
            continue
        out[hid] = normalize_profile(hid, raw, f"manifest:{path.name}")
    return out


def load_analysis_root(root: Optional[Path]) -> Dict[str, MonsterProfile]:
    if not root or not root.exists():
        return {}
    out: Dict[str, MonsterProfile] = {}
    for path in root.rglob("CURSOR_PROFILE.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            hid = str(raw.get("hpr", raw.get("id", path.parent.name))).strip()
            out[hid] = normalize_profile(hid, raw, f"analysis:{path}")
        except Exception as exc:
            print(f"WARN profile {path}: {exc}", file=sys.stderr)
    # Some old batches only contain PROFILE_SOURCE.json.
    for path in root.rglob("PROFILE_SOURCE.json"):
        hid = path.parent.name
        if hid in out:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            hid = str(raw.get("hpr", raw.get("id", hid))).strip()
            out[hid] = normalize_profile(hid, raw, f"analysis-source:{path}")
        except Exception:
            pass
    return out


def load_semantics(path: Optional[Path]) -> Dict[Tuple[str, str], Dict[str, str]]:
    out: Dict[Tuple[str, str], Dict[str, str]] = {}
    if not path or not path.exists():
        return out
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            hid = (row.get("hpr") or row.get("id") or "").strip()
            action = (row.get("visual_action") or row.get("action") or "").strip()
            if hid and action:
                out[(hid, action)] = {k: (v or "").strip() for k, v in row.items()}
    return out


def apply_semantics(profile: MonsterProfile, overrides: Dict[Tuple[str, str], Dict[str, str]]) -> None:
    for action in profile.actions:
        row = overrides.get((profile.hpr, action.visual_action))
        if not row:
            continue
        if row.get("semantic"):
            action.semantic = row["semantic"]
            action.semantic_source = "SEMANTICS_OVERRIDES.csv"
        if row.get("holley_name"):
            action.holley_name = row["holley_name"]


# ---------------------------------------------------------------------------
# HPR image-table reader
# ---------------------------------------------------------------------------

def detect_hpr_version(data: bytes) -> Tuple[Optional[int], str]:
    off = len(SIGNATURE)
    if len(data) <= off:
        return None, "missing"
    if data[off] in (2, 3):
        return int(data[off]), "u8@12"
    if len(data) >= off + 2:
        value = struct.unpack_from("<H", data, off)[0]
        if value in (2, 3):
            return int(value), "u16@12"
    if len(data) >= off + 4:
        value = struct.unpack_from("<I", data, off)[0]
        if value in (2, 3):
            return int(value), "u32@12"
    return None, "unknown"


def unpack_record(layout: HprRecordLayout, data: bytes, offset: int) -> Tuple[Tuple[int, ...], int]:
    end = offset + layout.size
    if offset < 0 or end > len(data):
        raise HprError("record outside file")
    values = struct.unpack_from(layout.fmt, data, offset)
    return tuple(int(x) for x in values), end


def parse_record_values(layout: HprRecordLayout, values: Tuple[int, ...]) -> Tuple[int, int, int, int, int, int, int, int, int]:
    if layout.has_mask:
        width, height, x, y, shadow_x, shadow_y, shadow_type, mask, compressed = values
    else:
        width, height, x, y, shadow_x, shadow_y, shadow_type, compressed = values
        mask = 0
    return width, height, x, y, shadow_x, shadow_y, shadow_type, mask, compressed


def parse_image_table_from(data: bytes, start: int, layout: HprRecordLayout, decode_pixels: bool = True) -> Optional[List[HprImage]]:
    images: List[HprImage] = []
    offset = start
    index = 0
    present_count = 0
    try:
        while offset < len(data):
            record_offset = offset
            values, payload_offset = unpack_record(layout, data, offset)
            width, height, x, y, sx, sy, st, mask, compressed = parse_record_values(layout, values)

            # Strict limits prevent accidental parsing of header bytes as images.
            if width < 0 or height < 0 or width > 8192 or height > 8192:
                return None
            if compressed < 0 or compressed > len(data):
                return None

            if compressed == 0:
                # Empty image slots are permitted.  They normally have zero size.
                if width not in (0, 1) or height not in (0, 1):
                    return None
                images.append(HprImage(index=index, present=False, width=width, height=height,
                                       x=x, y=y, shadow_x=sx, shadow_y=sy,
                                       shadow_type=st, mask=mask,
                                       compressed_length=0, record_offset=record_offset,
                                       payload_offset=payload_offset))
                offset = payload_offset
                index += 1
                continue

            if width <= 0 or height <= 0:
                return None
            end = payload_offset + compressed
            if end > len(data):
                return None
            payload = data[payload_offset:end]
            if not payload.startswith(b"\x1f\x8b"):
                return None
            try:
                raw = gzip.decompress(payload)
            except Exception:
                return None
            expected = width * height * 4
            if len(raw) != expected:
                return None
            rgba: Optional[bytes] = None
            if decode_pixels:
                # HPR stores BGRA32. Pillow and ZL PNG use RGBA.
                ba = bytearray(raw)
                ba[0::4], ba[2::4] = ba[2::4], ba[0::4]
                rgba = bytes(ba)
            images.append(HprImage(index=index, present=True, width=width, height=height,
                                   x=x, y=y, shadow_x=sx, shadow_y=sy,
                                   shadow_type=st, mask=mask,
                                   compressed_length=compressed,
                                   record_offset=record_offset,
                                   payload_offset=payload_offset, rgba=rgba))
            present_count += 1
            offset = end
            index += 1

        if offset != len(data) or present_count == 0:
            return None
        return images
    except (struct.error, HprError, OverflowError, MemoryError):
        return None


def discover_image_table(data: bytes, decode_pixels: bool = True) -> Tuple[int, HprRecordLayout, List[HprImage]]:
    if not data.startswith(SIGNATURE):
        raise HprError("Not a HispaCrystal HPR (signature missing)")

    # Gzip magic gives us a reliable anchor.  For each valid-looking payload,
    # test the record immediately before it, then backtrack over possible empty
    # records.  The accepted candidate must parse cleanly to EOF.
    gzip_positions: List[int] = []
    pos = 0
    while True:
        pos = data.find(b"\x1f\x8b", pos)
        if pos < 0:
            break
        gzip_positions.append(pos)
        pos += 2
    if not gzip_positions:
        raise HprError("No gzip image payloads found")

    candidates: List[Tuple[int, int, int, HprRecordLayout, List[HprImage]]] = []
    min_header = len(SIGNATURE) + 1
    for layout in HPR_RECORD_LAYOUTS:
        size = layout.size
        for gz in gzip_positions[:64]:  # first anchors are enough and keep scans cheap
            immediate = gz - size
            if immediate < min_header:
                continue
            # The first gzip may be preceded by empty slots. Test up to 512 of them.
            for empty_count in range(0, 513):
                start = immediate - empty_count * size
                if start < min_header:
                    break
                images = parse_image_table_from(data, start, layout, decode_pixels=decode_pixels)
                if images is None:
                    continue
                present = sum(1 for x in images if x.present)
                # Prefer more slots/present images and an earlier image table.
                candidates.append((len(images), present, -start, layout, images))
                break
            if candidates:
                # Do not need to try every gzip anchor after a proven suffix for this layout.
                break

    if not candidates:
        raise HprError(
            "HispaCrystal signature found but the image record layout could not be verified. "
            "No data were guessed; this library must be added as a new record layout."
        )
    candidates.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
    _, _, neg_start, layout, images = candidates[0]
    return -neg_start, layout, images


def parse_hpr(path: Path, profile: Optional[MonsterProfile], semantics: Dict[Tuple[str, str], Dict[str, str]]) -> ParsedHpr:
    data = path.read_bytes()
    if not data.startswith(SIGNATURE):
        raise HprError(f"{path.name}: signature {SIGNATURE!r} not found")
    version, version_encoding = detect_hpr_version(data)
    image_offset, layout, images = discover_image_table(data, decode_pixels=True)
    hid = hpr_id_from_path(path)
    present = sum(1 for x in images if x.present)

    if profile is None:
        profile = MonsterProfile(
            hpr=hid,
            status="REVIEW_FRAMESET_UNKNOWN",
            slot_count=len(images),
            nonempty_image_count=present,
            issues=["FrameSet profile is not proven. Provide --analysis-root or --manifest."],
            source="raw-hpr:image-table-only",
        )
    else:
        profile = MonsterProfile(**{**asdict(profile), "actions": profile.actions})
        # asdict above recursively converts actions, so rebuild the profile safely.
        # This branch is immediately replaced below with an explicit copy.
        profile = MonsterProfile(
            hpr=profile.hpr,
            status=profile.status,
            slot_count=profile.slot_count,
            nonempty_image_count=profile.nonempty_image_count,
            actions=[ActionProfile(**asdict(a)) if isinstance(a, ActionProfile) else normalize_action(a, i + 1)
                     for i, a in enumerate(profile.actions)],
            effects=list(profile.effects),
            unreferenced_nonempty_ranges=list(profile.unreferenced_nonempty_ranges),
            issues=list(profile.issues),
            warnings=list(profile.warnings),
            source=profile.source,
        )

    # Raw image truth wins for counts; mismatches are surfaced, never hidden.
    if profile.slot_count and profile.slot_count != len(images):
        profile.warnings.append(f"Profile slot_count={profile.slot_count}, HPR parsed slots={len(images)}")
    if profile.nonempty_image_count and profile.nonempty_image_count != present:
        profile.warnings.append(
            f"Profile nonempty_image_count={profile.nonempty_image_count}, HPR parsed present={present}"
        )
    profile.slot_count = len(images)
    profile.nonempty_image_count = present
    apply_semantics(profile, semantics)
    validate_actions(profile, images)
    profile.unreferenced_nonempty_ranges = calculate_unreferenced_ranges(profile, images)

    return ParsedHpr(
        path=path,
        hpr_id=hid,
        version=version,
        version_encoding=version_encoding,
        image_table_offset=image_offset,
        image_record_layout=layout.name,
        images=images,
        profile=profile,
        source_sha256=sha256_bytes(data),
    )


# ---------------------------------------------------------------------------
# Action mapping / validation
# ---------------------------------------------------------------------------

def action_direction_indices(action: ActionProfile, slot_count: int) -> Dict[str, List[int]]:
    result: Dict[str, List[int]] = {}
    if action.count <= 0 or action.stride <= 0:
        return result
    for direction, name in enumerate(HPR_DIRECTION_NAMES):
        start = action.start + direction * action.stride
        indexes = [start + frame for frame in range(action.count) if 0 <= start + frame < slot_count]
        if indexes:
            result[name] = indexes
    return result


def action_all_indices(action: ActionProfile, slot_count: int) -> List[int]:
    values: List[int] = []
    for indexes in action_direction_indices(action, slot_count).values():
        values.extend(indexes)
    return sorted(set(values))


def validate_actions(profile: MonsterProfile, images: Sequence[HprImage]) -> None:
    slots = len(images)
    for action in profile.actions:
        if action.start < 0 or action.start >= slots:
            profile.issues.append(f"{action.visual_action}: start {action.start} outside library ({slots})")
            continue
        if action.count <= 0:
            profile.issues.append(f"{action.visual_action}: frame count is {action.count}")
        if action.stride <= 0:
            profile.issues.append(f"{action.visual_action}: stride is {action.stride}")
            continue
        dirs = action_direction_indices(action, slots)
        complete = [name for name, ids in dirs.items() if len(ids) == action.count]
        if len(complete) < 8:
            profile.warnings.append(
                f"{action.visual_action}: {len(complete)}/8 complete directions stored ({', '.join(complete)})"
            )


def calculate_unreferenced_ranges(profile: MonsterProfile, images: Sequence[HprImage]) -> List[Dict[str, int]]:
    referenced: set[int] = set()
    for action in profile.actions:
        referenced.update(action_all_indices(action, len(images)))
        if action.effect_start is not None and action.effect_count and action.effect_stride:
            for direction in range(8):
                base = action.effect_start + direction * action.effect_stride
                referenced.update(base + i for i in range(action.effect_count) if 0 <= base + i < len(images))
    present = {image.index for image in images if image.present}
    return contiguous_ranges(present - referenced)


def profile_json(parsed: ParsedHpr) -> Dict[str, Any]:
    actions = []
    for action in parsed.profile.actions:
        item = asdict(action)
        item["source_indices_by_direction"] = action_direction_indices(action, len(parsed.images))
        item["source_indices"] = action_all_indices(action, len(parsed.images))
        actions.append(item)
    return {
        "format_version": 2,
        "hpr": parsed.hpr_id,
        "source_hpr": parsed.path.name,
        "source_sha256": parsed.source_sha256,
        "hpr_version": parsed.version,
        "hpr_version_encoding": parsed.version_encoding,
        "image_record_layout": parsed.image_record_layout,
        "image_table_offset": parsed.image_table_offset,
        "slot_count": len(parsed.images),
        "nonempty_image_count": sum(1 for x in parsed.images if x.present),
        "status": parsed.profile.status,
        "profile_source": parsed.profile.source,
        "direction_order_hpr": HPR_DIRECTION_NAMES,
        "mir2_to_zircon_direction_shift": MIR2_TO_ZIRCON_DIRECTION_SHIFT,
        "direction_policy": "source indexes preserved; Cursor/Zircon must apply the documented direction shift",
        "visual_semantics_rule": "Attack/Range/Spell/Special labels are visual only unless semantic_source proves behaviour",
        "actions": actions,
        "effects": parsed.profile.effects,
        "unreferenced_nonempty_ranges": parsed.profile.unreferenced_nonempty_ranges,
        "issues": parsed.profile.issues,
        "warnings": parsed.profile.warnings,
    }


# ---------------------------------------------------------------------------
# ZL2 writer (inverse of TOOLS/zl_extractor/zl_extract.py)
# ---------------------------------------------------------------------------

def build_zl2(images: Sequence[HprImage], output: Path) -> Dict[str, Any]:
    payloads: Dict[int, bytes] = {}
    for image in images:
        if image.present:
            payloads[image.index] = image.png_bytes()

    # Header is fixed-size: b'ZL2' + <iiiBBhqiqi> = 43 bytes.
    header_size = 43
    cursor = header_size
    entry_rows: List[Tuple[int, int, int, int, int, int, int]] = []
    payload_blob = bytearray()
    for image in images:
        if not image.present:
            continue
        payload = payloads[image.index]
        entry_rows.append((ZL_ENTRY_IMAGE, image.index, len(payload), len(payload), cursor,
                           ZL_COMPRESSION_NONE, ZL_CODEC_PNG))
        payload_blob.extend(payload)
        cursor += len(payload)

    metadata = bytearray()
    metadata.extend(struct.pack("<iiii", ZL2_VERSION, len(images), 0, 0))
    for image in images:
        if not image.present:
            metadata.extend(struct.pack("<B", 0))
            continue
        png = payloads[image.index]
        metadata.extend(struct.pack("<B", 1))
        metadata.extend(struct.pack(
            "<ihhhhBhhhhhh",
            image.index, image.width, image.height, image.x, image.y,
            image.shadow_type & 0xFF,
            0, 0, image.shadow_x, image.shadow_y, 0, 0,
        ))
        metadata.extend(struct.pack("<i", -1))  # atlas page: none
        metadata.extend(struct.pack("<hhhh", 0, 0, 0, 0))
        metadata.extend(struct.pack("<hhhh", 0, 0, 0, 0))
        metadata.extend(struct.pack(
            "<BBBBBB",
            ZL_CODEC_PNG, ZL_CODEC_PNG, ZL_CODEC_PNG,
            ZL_RUNTIME_SOURCE, ZL_RUNTIME_SOURCE, ZL_RUNTIME_SOURCE,
        ))
        metadata.extend(struct.pack(
            "<iiiiiiiii",
            len(png), 0, 0,  # main stored/bc7/fallback
            0, 0, 0,         # shadow
            0, 0, 0,         # overlay
        ))

    metadata_offset = header_size + len(payload_blob)
    index = bytearray()
    index.extend(struct.pack("<i", len(entry_rows)))
    for typ, eid, unc, comp, pos, compression, codec in entry_rows:
        index.extend(struct.pack("<BiiiqBB", typ, eid, unc, comp, pos, compression, codec))
    index_offset = metadata_offset + len(metadata)

    header = b"ZL2" + struct.pack(
        "<iiiBBhqiqi",
        ZL2_VERSION, len(images), 0,
        ZL_CODEC_PNG, 0, 0,
        metadata_offset, len(metadata),
        index_offset, len(index),
    )
    if len(header) != header_size:
        raise ZlError(f"internal ZL2 header size {len(header)} != {header_size}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(header + payload_blob + metadata + index)
    validation = validate_zl2(output)
    return validation


def validate_zl2(path: Path) -> Dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 43 or not data.startswith(b"ZL2"):
        raise ZlError("written file is not a ZL2 container")
    values = struct.unpack_from("<iiiBBhqiqi", data, 3)
    version, count, atlas, default_codec, flags, reserved, mo, ms, ioff, isz = values
    if version < 2:
        raise ZlError(f"invalid ZL2 version {version}")
    if not (43 <= mo <= len(data)) or mo + ms > len(data):
        raise ZlError("metadata range outside file")
    if not (mo + ms <= ioff <= len(data)) or ioff + isz > len(data):
        raise ZlError("index range outside file")
    idx = data[ioff:ioff + isz]
    if len(idx) < 4:
        raise ZlError("truncated ZL2 index")
    entry_count = struct.unpack_from("<i", idx, 0)[0]
    off = 4
    entries: List[Tuple[int, int, int, int, int, int, int]] = []
    for _ in range(entry_count):
        if off + 23 > len(idx):
            raise ZlError("truncated ZL2 index entry")
        row = struct.unpack_from("<BiiiqBB", idx, off)
        off += 23
        entries.append(tuple(int(x) for x in row))
    if off != len(idx):
        raise ZlError("ZL2 index length mismatch")
    for typ, eid, unc, comp, pos, compression, codec in entries:
        if pos < 43 or pos + comp > mo:
            raise ZlError(f"entry {eid}: payload outside data section")
        if compression != ZL_COMPRESSION_NONE:
            raise ZlError(f"entry {eid}: unexpected compression {compression}")
        if codec != ZL_CODEC_PNG:
            raise ZlError(f"entry {eid}: unexpected codec {codec}")
        payload = data[pos:pos + comp]
        if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ZlError(f"entry {eid}: PNG signature missing")
    return {
        "format": "ZL2",
        "version": version,
        "slot_count": count,
        "entry_count": entry_count,
        "default_codec": default_codec,
        "size_bytes": len(data),
        "sha256": sha256_bytes(data),
    }


# ---------------------------------------------------------------------------
# Per-monster artifacts
# ---------------------------------------------------------------------------

def write_image_metadata(parsed: ParsedHpr, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "index", "present", "width", "height", "x", "y", "shadow_x", "shadow_y",
        "shadow_type", "mask", "compressed_length", "record_offset", "payload_offset"
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for image in parsed.images:
            row = asdict(image)
            row.pop("rgba", None)
            writer.writerow({k: row.get(k) for k in fields})


def write_pngs(parsed: ParsedHpr, root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for image in parsed.images:
        if not image.present:
            continue
        (root / f"{image.index:06d}.png").write_bytes(image.png_bytes())


def frame_constructor(action: ActionProfile) -> str:
    return (
        f"new Frame({action.start}, {action.count}, {action.stride}, "
        f"TimeSpan.FromMilliseconds({action.delay_ms}))"
    )


def write_frameset_cs(parsed: ParsedHpr, path: Path) -> None:
    lines = [
        "// Generated by ORIGINS HPR -> Zircon Monster Builder.",
        "// Visual mapping only. Do NOT infer server AI/damage/range/heal from Combat slots.",
        f"// HPR {parsed.hpr_id}; Mir2->Zircon direction shift = {MIR2_TO_ZIRCON_DIRECTION_SHIFT}.",
        "// Register this profile for this MonsterImage only. Never replace FrameSet.DefaultMonster globally.",
        "",
        "var frames = new Dictionary<MirAnimation, Frame>",
        "{",
    ]
    for action in parsed.profile.actions:
        slot = action.zircon_animation_slot
        lines.append(f"    [MirAnimation.{slot}] = {frame_constructor(action)}, // {action.visual_action}")
    lines.extend([
        "};",
        "",
        f"// Direction rule: targetDir -> sourceDir = (targetDir + {MIR2_TO_ZIRCON_DIRECTION_SHIFT}) % 8",
        "// Keep server behaviour/Race/AI in a separate mapping.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation(parsed: ParsedHpr, zl_validation: Optional[Dict[str, Any]], path: Path) -> None:
    lines = [
        f"HPR: {parsed.hpr_id}",
        f"Source: {parsed.path}",
        f"SHA256: {parsed.source_sha256}",
        f"Hispa version: {parsed.version} ({parsed.version_encoding})",
        f"Image record layout: {parsed.image_record_layout}",
        f"Image table offset: 0x{parsed.image_table_offset:X}",
        f"Slots: {len(parsed.images)}",
        f"Non-empty images: {sum(1 for x in parsed.images if x.present)}",
        f"Profile status: {parsed.profile.status}",
        f"Profile source: {parsed.profile.source}",
        f"Actions: {len(parsed.profile.actions)}",
        f"Direction shift Mir2->Zircon: {MIR2_TO_ZIRCON_DIRECTION_SHIFT}",
    ]
    if zl_validation:
        lines += [
            "",
            "ZL2 VALIDATION: OK",
            f"ZL slots: {zl_validation['slot_count']}",
            f"ZL entries: {zl_validation['entry_count']}",
            f"ZL size: {zl_validation['size_bytes']}",
            f"ZL SHA256: {zl_validation['sha256']}",
        ]
    lines += ["", "ISSUES:"] + ([f"- {x}" for x in parsed.profile.issues] or ["- none"])
    lines += ["", "WARNINGS:"] + ([f"- {x}" for x in parsed.profile.warnings] or ["- none"])
    lines += ["", "UNREFERENCED NON-EMPTY GRAPHICS:"]
    if parsed.profile.unreferenced_nonempty_ranges:
        for item in parsed.profile.unreferenced_nonempty_ranges:
            lines.append(f"- {item['start']}..{item['end']} ({item['count']})")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_cursor_import(parsed: ParsedHpr, zl_name: str, path: Path) -> None:
    unknown = [a.visual_action for a in parsed.profile.actions if a.semantic == "UNKNOWN_VISUAL_ONLY"]
    text = f"""# CURSOR IMPORT - HISPA HPR {parsed.hpr_id}

This folder was generated from `{parsed.path.name}` by the ORIGINS HPR -> Zircon Monster Builder.

## Files Cursor must read first

- `{zl_name}` - Zircon ZL2 image library, source slot IDs preserved.
- `CURSOR_PROFILE.json` - exact visual action layout and image IDs by direction.
- `IMAGE_METADATA.csv` - source dimensions and X/Y/shadow offsets for every slot.
- `FRAMESET.cs.txt` - isolated FrameSet snippet.
- `VALIDATION.txt` - parser/writer validation and review notes.

## Mandatory rules

1. The user chooses the final `MonsterImage`, `Mon-XX` and slot. Do not invent another target.
2. Do **not** modify `FrameSet.DefaultMonster` globally. Register this profile only for the chosen MonsterImage.
3. Original HPR image indexes are preserved inside the generated `.Zl`; do not compact or renumber them.
4. Preserve X/Y metadata. It is already written to `.Zl` and listed in `IMAGE_METADATA.csv`.
5. HPR direction order is `{', '.join(HPR_DIRECTION_NAMES)}`. ORIGINS uses `Mir2DirMap.Shift = {MIR2_TO_ZIRCON_DIRECTION_SHIFT}`. Apply that direction mapping in the monster-specific renderer/profile; do not physically guess rotations.
6. `Combat1`, `Combat2`, etc. are visual containers only. They do not prove damage, range, projectile, heal, spell or AI behaviour.
7. Unreferenced non-empty images are candidates for effects/projectiles/overlays. Do not attach them automatically without evidence.
8. Keep server Race/AI/stats separate from this visual import.

## Behaviour still unknown

{', '.join(unknown) if unknown else 'No UNKNOWN_VISUAL_ONLY actions in the supplied profile.'}

## Cursor completion report

When importing, report:
- final MonsterImage;
- final Mon/Zl file and slot;
- FrameSet registration location;
- direction-shift implementation;
- server behaviour still unmapped;
- any indices or offsets that were changed (normally: none).
"""
    path.write_text(text, encoding="utf-8")


def build_one(parsed: ParsedHpr, out_root: Path, write_zl: bool, export_png: bool) -> BuildResult:
    monster_dir = out_root / "MONSTERS" / parsed.hpr_id
    monster_dir.mkdir(parents=True, exist_ok=True)
    (monster_dir / "CURSOR_PROFILE.json").write_text(
        json.dumps(profile_json(parsed), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_image_metadata(parsed, monster_dir / "IMAGE_METADATA.csv")
    write_frameset_cs(parsed, monster_dir / "FRAMESET.cs.txt")

    zl_validation: Optional[Dict[str, Any]] = None
    zl_name = f"Hispa_{parsed.hpr_id}.Zl"
    if write_zl:
        zl_validation = build_zl2(parsed.images, monster_dir / zl_name)
    if export_png:
        write_pngs(parsed, monster_dir / "FRAMES_PNG")
    write_validation(parsed, zl_validation, monster_dir / "VALIDATION.txt")
    write_cursor_import(parsed, zl_name, monster_dir / "CURSOR_IMPORT_THIS_MONSTER.md")

    actions = ",".join(a.visual_action for a in parsed.profile.actions)
    unknown = ",".join(a.visual_action for a in parsed.profile.actions if a.semantic == "UNKNOWN_VISUAL_ONLY")
    unref = sum(int(x.get("count", 0)) for x in parsed.profile.unreferenced_nonempty_ranges)
    return BuildResult(
        hpr=parsed.hpr_id,
        source_file=parsed.path.name,
        source_sha256=parsed.source_sha256,
        hpr_version=parsed.version,
        image_layout=parsed.image_record_layout,
        slot_count=len(parsed.images),
        present_count=sum(1 for x in parsed.images if x.present),
        status=parsed.profile.status,
        profile_source=parsed.profile.source,
        action_count=len(parsed.profile.actions),
        actions=actions,
        unknown_behavior_actions=unknown,
        unreferenced_graphics=unref,
        zl_file=str(Path("MONSTERS") / parsed.hpr_id / zl_name) if write_zl else "",
        output_folder=str(Path("MONSTERS") / parsed.hpr_id),
        issues=" | ".join(parsed.profile.issues),
        warnings=" | ".join(parsed.profile.warnings),
    )


# ---------------------------------------------------------------------------
# Master sheets
# ---------------------------------------------------------------------------

def write_master_sheets(results: Sequence[BuildResult], out_root: Path) -> None:
    rows = sorted(results, key=lambda x: natural_key(x.hpr))
    fields = list(BuildResult.__dataclass_fields__.keys())
    with (out_root / "MASTER_SHEET.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in rows:
            writer.writerow(asdict(result))
    (out_root / "MASTER_SHEET.json").write_text(
        json.dumps([asdict(x) for x in rows], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    html_rows = []
    for r in rows:
        css = "review" if r.status.startswith("REVIEW") or r.issues else "auto"
        html_rows.append(
            "<tr class='%s'>" % css
            + "".join(
                f"<td>{html.escape(str(value if value is not None else ''))}</td>"
                for value in [
                    r.hpr, r.status, r.slot_count, r.present_count, r.action_count, r.actions,
                    r.unknown_behavior_actions, r.unreferenced_graphics, r.image_layout,
                    r.profile_source, r.issues, r.warnings, r.output_folder,
                ]
            )
            + "</tr>"
        )
    doc = """<!doctype html><html><head><meta charset='utf-8'><title>ORIGINS HPR Master Sheet</title>
<style>body{font-family:Segoe UI,Arial,sans-serif;background:#111;color:#ddd;margin:20px}input{width:420px;padding:8px;margin-bottom:12px;background:#222;color:#fff;border:1px solid #555}table{border-collapse:collapse;width:100%;font-size:12px}th,td{border:1px solid #333;padding:6px;vertical-align:top}th{position:sticky;top:0;background:#222}.review{background:#321d1d}.auto{background:#142619}code{color:#9dd}</style></head><body>
<h1>ORIGINS HPR -> Zircon Master Sheet</h1><p>Attack/Range/Spell/Special names are visual only unless an explicit semantic override proves behaviour.</p>
<input id='q' placeholder='Filter by ID, status, action, issue...' oninput='f()'><table id='t'><thead><tr>
<th>HPR</th><th>Status</th><th>Slots</th><th>Present</th><th>Actions #</th><th>Actions</th><th>Unknown behaviour</th><th>Unreferenced</th><th>HPR image layout</th><th>Profile source</th><th>Issues</th><th>Warnings</th><th>Folder</th></tr></thead><tbody>""" + "\n".join(html_rows) + """</tbody></table>
<script>function f(){let q=document.getElementById('q').value.toLowerCase();for(let r of document.querySelectorAll('#t tbody tr'))r.style.display=r.innerText.toLowerCase().includes(q)?'':'none';}</script></body></html>"""
    (out_root / "MASTER_SHEET.html").write_text(doc, encoding="utf-8")


def write_batch_summary(results: Sequence[BuildResult], failures: Sequence[Dict[str, str]], out_root: Path) -> None:
    total = len(results)
    reviews = sum(1 for r in results if r.status.startswith("REVIEW") or r.issues)
    lines = [
        "ORIGINS HPR -> ZIRCON BATCH SUMMARY",
        f"Processed successfully: {total}",
        f"Review/issue cases: {reviews}",
        f"Failed HPR reads: {len(failures)}",
        f"Total slots: {sum(r.slot_count for r in results)}",
        f"Total present images: {sum(r.present_count for r in results)}",
        "",
        "Failures:",
    ]
    lines.extend([f"- {x['file']}: {x['error']}" for x in failures] or ["- none"])
    (out_root / "BATCH_SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_root / "FAILURES.json").write_text(json.dumps(list(failures), indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Input discovery / batch runner
# ---------------------------------------------------------------------------

def collect_hpr_files(inputs: Sequence[Path], temp_root: Path) -> List[Path]:
    out: List[Path] = []
    for source in inputs:
        if source.is_dir():
            out.extend(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() == ".hpr")
        elif source.is_file() and source.suffix.lower() == ".hpr":
            out.append(source)
        elif source.is_file() and source.suffix.lower() == ".zip":
            dest = temp_root / source.stem
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(source, "r") as archive:
                for info in archive.infolist():
                    if Path(info.filename).suffix.lower() != ".hpr":
                        continue
                    # Ignore unsafe paths.
                    name = Path(info.filename).name
                    target = dest / name
                    with archive.open(info) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    out.append(target)
        else:
            raise FileNotFoundError(source)
    # Deduplicate exact paths and sort naturally.
    unique = {str(p.resolve()): p for p in out}
    return sorted(unique.values(), key=lambda p: natural_key(p.stem))


def choose_profile(hid: str, analysis: Dict[str, MonsterProfile], manifest: Dict[str, MonsterProfile]) -> Optional[MonsterProfile]:
    return analysis.get(hid) or manifest.get(hid)


def run_batch(args: argparse.Namespace) -> int:
    out_root: Path = args.out
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(args.manifest)
    analysis = load_analysis_root(args.analysis_root)
    semantics = load_semantics(args.semantics)

    results: List[BuildResult] = []
    failures: List[Dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="origins_hpr_") as temp:
        files = collect_hpr_files(args.inputs, Path(temp))
        if not files:
            raise SystemExit("No .hpr files found")
        print(f"Found {len(files)} HPR libraries")
        for index, path in enumerate(files, 1):
            hid = hpr_id_from_path(path)
            print(f"[{index}/{len(files)}] {hid} ...", flush=True)
            try:
                parsed = parse_hpr(path, choose_profile(hid, analysis, manifest), semantics)
                result = build_one(parsed, out_root, write_zl=not args.no_zl, export_png=args.export_png)
                results.append(result)
                print(
                    f"  OK slots={result.slot_count} present={result.present_count} "
                    f"actions={result.action_count} status={result.status}"
                )
            except Exception as exc:
                failures.append({"file": str(path), "hpr": hid, "error": str(exc)})
                print(f"  REVIEW/FAIL: {exc}", file=sys.stderr)
                if args.trace:
                    traceback.print_exc()
                if args.stop_on_error:
                    raise

    write_master_sheets(results, out_root)
    write_batch_summary(results, failures, out_root)
    print(f"\nDone. Master sheet: {out_root / 'MASTER_SHEET.html'}")
    print(f"Successful: {len(results)} | Failed: {len(failures)}")
    return 1 if failures and args.fail_exit_code else 0


def run_inspect(args: argparse.Namespace) -> int:
    semantics = load_semantics(args.semantics)
    manifest = load_manifest(args.manifest)
    analysis = load_analysis_root(args.analysis_root)
    hid = hpr_id_from_path(args.hpr)
    parsed = parse_hpr(args.hpr, choose_profile(hid, analysis, manifest), semantics)
    obj = profile_json(parsed)
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="origins_hpr_zircon",
        description="Analyze HispaCrystal HPR libraries, build Zircon ZL2 monster assets and MasterSheet metadata.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def shared(p: argparse.ArgumentParser) -> None:
        p.add_argument("--analysis-root", type=Path, help="Old analyzer output root containing CURSOR_PROFILE.json files")
        p.add_argument("--manifest", type=Path, help="ALL_MONSTERS_CURSOR_MANIFEST.json or equivalent")
        p.add_argument("--semantics", type=Path, default=Path(__file__).with_name("SEMANTICS_OVERRIDES.csv"),
                       help="Confirmed server-semantics overrides; never inferred automatically")

    batch = sub.add_parser("batch", help="Process one or more HPR files/folders/ZIPs")
    batch.add_argument("inputs", nargs="+", type=Path)
    batch.add_argument("--out", type=Path, default=Path("OUTPUT_HISPA_ZIRCON"))
    batch.add_argument("--no-zl", action="store_true", help="Analyze only; do not write .Zl")
    batch.add_argument("--export-png", action="store_true", help="Also export every frame as PNG (not required for ZL)")
    batch.add_argument("--stop-on-error", action="store_true")
    batch.add_argument("--fail-exit-code", action="store_true", help="Return exit code 1 if any HPR fails")
    batch.add_argument("--trace", action="store_true")
    shared(batch)
    batch.set_defaults(func=run_batch)

    inspect = sub.add_parser("inspect", help="Print one HPR profile as JSON without writing output")
    inspect.add_argument("hpr", type=Path)
    shared(inspect)
    inspect.set_defaults(func=run_inspect)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
