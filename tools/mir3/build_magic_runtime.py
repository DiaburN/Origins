#!/usr/bin/env python3
"""Build the ORIGINS X magic-menu runtime from the user's real Zircon data.

Sources:
  - System.db  -> MagicInfo values (name, icon, required levels, EXP, description...)
  - MIcon.Zl   -> exact 36x36 magic icons

Nothing is invented. The generated runtime is local browser data only.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import struct
from pathlib import Path

from build_full_zircon_ui import ZLLibrary, candidate_roots, pack


def read_exact(stream: io.BufferedIOBase | io.BytesIO, size: int) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise EOFError(f"Unexpected end of file while reading {size} bytes")
    return data


def read_i32(stream):
    return struct.unpack("<i", read_exact(stream, 4))[0]


def read_7bit_int(stream):
    value = 0
    shift = 0
    while shift < 35:
        byte = read_exact(stream, 1)[0]
        value |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            return value
        shift += 7
    raise ValueError("Invalid .NET 7-bit encoded integer")


def read_dotnet_string(stream):
    length = read_7bit_int(stream)
    if length < 0 or length > 16_000_000:
        raise ValueError(f"Invalid .NET string length: {length}")
    return read_exact(stream, length).decode("utf-8")


def find_source_file(repo: Path, explicit: Path | None, names: list[str]) -> Path:
    wanted = {name.lower() for name in names}

    for root in candidate_roots(repo, explicit):
        direct_candidates = [root, root / "Data", root / "Database", root / "Server" / "Database"]
        for folder in direct_candidates:
            if not folder.exists():
                continue
            for name in names:
                path = folder / name
                if path.is_file():
                    return path

        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            try:
                depth = len(current_path.relative_to(root).parts)
            except ValueError:
                depth = 99

            dirs[:] = [
                d for d in dirs
                if d not in {".git", "node_modules", "__pycache__", "bin", "obj"}
                and not d.startswith(".")
            ]
            if depth > 6:
                dirs[:] = []
                continue

            lower = {name.lower(): name for name in files}
            for wanted_name in wanted:
                hit = lower.get(wanted_name)
                if hit:
                    return current_path / hit

    raise FileNotFoundError(" / ".join(names))


def read_value(stream: io.BytesIO, type_name: str):
    if type_name == "System.Boolean":
        return bool(read_exact(stream, 1)[0])
    if type_name == "System.Byte":
        return read_exact(stream, 1)[0]
    if type_name == "System.SByte":
        return struct.unpack("<b", read_exact(stream, 1))[0]
    if type_name == "System.Int16":
        return struct.unpack("<h", read_exact(stream, 2))[0]
    if type_name == "System.UInt16":
        return struct.unpack("<H", read_exact(stream, 2))[0]
    if type_name == "System.Int32":
        return struct.unpack("<i", read_exact(stream, 4))[0]
    if type_name == "System.UInt32":
        return struct.unpack("<I", read_exact(stream, 4))[0]
    if type_name == "System.Int64":
        return struct.unpack("<q", read_exact(stream, 8))[0]
    if type_name == "System.UInt64":
        return struct.unpack("<Q", read_exact(stream, 8))[0]
    if type_name == "System.Single":
        return struct.unpack("<f", read_exact(stream, 4))[0]
    if type_name == "System.Double":
        return struct.unpack("<d", read_exact(stream, 8))[0]
    if type_name == "System.Decimal":
        # Decimal is not used by MagicInfo, but consuming 16 bytes keeps parsing correct.
        read_exact(stream, 16)
        return None
    if type_name == "System.String":
        return read_dotnet_string(stream)
    if type_name in {"System.DateTime", "System.TimeSpan"}:
        return struct.unpack("<q", read_exact(stream, 8))[0]
    if type_name == "System.Drawing.Color":
        return struct.unpack("<i", read_exact(stream, 4))[0]
    if type_name in {"System.Drawing.Point", "System.Drawing.Size"}:
        return list(struct.unpack("<ii", read_exact(stream, 8)))
    if type_name == "System.Byte[]":
        length = read_i32(stream)
        return list(read_exact(stream, length))
    if type_name == "System.Int32[]":
        exists = bool(read_exact(stream, 1)[0])
        if not exists:
            return None
        length = read_i32(stream)
        return [read_i32(stream) for _ in range(length)]
    if type_name == "System.Drawing.Point[]":
        exists = bool(read_exact(stream, 1)[0])
        if not exists:
            return None
        length = read_i32(stream)
        return [list(struct.unpack("<ii", read_exact(stream, 8))) for _ in range(length)]
    if type_name == "System.Collections.BitArray":
        exists = bool(read_exact(stream, 1)[0])
        if not exists:
            return None
        length = read_i32(stream)
        return list(read_exact(stream, length))

    raise ValueError(f"Unsupported MagicInfo property type: {type_name}")


def parse_magic_info(system_db: Path):
    with system_db.open("rb") as reader:
        mapping_count = read_i32(reader)
        if mapping_count <= 0 or mapping_count > 10_000:
            raise ValueError(
                "System.db does not look like an unencrypted Zircon MirDB database. "
                "If the database is encrypted, export MagicInfo from the server first."
            )

        mappings = []
        for _ in range(mapping_count):
            type_name = read_dotnet_string(reader)
            property_count = read_i32(reader)
            if property_count < 0 or property_count > 10_000:
                raise ValueError(f"Invalid property count in mapping {type_name}: {property_count}")
            properties = []
            for _ in range(property_count):
                properties.append((read_dotnet_string(reader), read_dotnet_string(reader)))
            mappings.append((type_name, properties))

        magic_mapping = None
        magic_data = None

        for type_name, properties in mappings:
            length = read_i32(reader)
            if length < 0 or length > 2_000_000_000:
                raise ValueError(f"Invalid collection size for {type_name}: {length}")
            data = read_exact(reader, length)
            if type_name.endswith(".MagicInfo"):
                magic_mapping = properties
                magic_data = data

    if magic_mapping is None or magic_data is None:
        raise ValueError("MagicInfo collection was not found inside System.db")

    stream = io.BytesIO(magic_data)
    _highest_index = read_i32(stream)
    count = read_i32(stream)
    records = []

    for _ in range(count):
        raw_length = read_i32(stream)
        raw = io.BytesIO(read_exact(stream, raw_length))
        record = {}
        for property_name, type_name in magic_mapping:
            record[property_name] = read_value(raw, type_name)
        records.append(record)

    return records


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build(repo: Path, source: Path | None):
    system_db = find_source_file(repo, source, ["System.db"])
    micon_path = find_source_file(repo, source, ["MIcon.Zl", "MIcon(1).Zl"])

    print(f"System.db: {system_db}")
    print(f"MIcon.Zl : {micon_path}")

    records = parse_magic_info(system_db)
    if not records:
        raise ValueError("System.db contains no MagicInfo rows")

    micon = ZLLibrary(micon_path)
    icon_indices = sorted({safe_int(row.get("Icon"), -1) for row in records if safe_int(row.get("Icon"), -1) >= 0})

    icon_items = []
    missing_icons = []
    for index in icon_indices:
        try:
            icon_items.append((f"icon-{index}", micon.decode(index)))
        except Exception:
            missing_icons.append(index)

    if not icon_items:
        raise ValueError("No referenced MagicInfo icons could be decoded from MIcon.Zl")

    out_dir = repo / "assets" / "ui" / "magic"
    out_dir.mkdir(parents=True, exist_ok=True)
    placements = pack(icon_items, out_dir / "micon-atlas.webp", 1024)

    icons = {}
    for name, (x, y, width, height) in placements.items():
        index = name.split("-", 1)[1]
        icons[index] = {"x": x, "y": y, "w": width, "h": height}

    by_magic_id = {}
    for row in records:
        magic_id = safe_int(row.get("Magic"), -1)
        if magic_id < 0:
            continue

        icon_index = safe_int(row.get("Icon"), -1)
        entry = {
            "name": row.get("Name") or f"Magic {magic_id}",
            "magicId": magic_id,
            "iconIndex": icon_index,
            "school": row.get("School"),
            "property": row.get("Property"),
            "needLevels": [
                safe_int(row.get("NeedLevel1")),
                safe_int(row.get("NeedLevel2")),
                safe_int(row.get("NeedLevel3")),
            ],
            "experience": [
                safe_int(row.get("Experience1")),
                safe_int(row.get("Experience2")),
                safe_int(row.get("Experience3")),
            ],
            "baseCost": safe_int(row.get("BaseCost")),
            "levelCost": safe_int(row.get("LevelCost")),
            "delay": safe_int(row.get("Delay")),
            "description": row.get("Description") or "",
        }
        if str(icon_index) in icons:
            entry["icon"] = icons[str(icon_index)]
        by_magic_id[str(magic_id)] = entry

    runtime = {
        "version": 1,
        "sheet": "assets/ui/magic/micon-atlas.webp",
        "source": {
            "systemDb": system_db.name,
            "micon": micon_path.name,
        },
        "icons": icons,
        "byMagicId": by_magic_id,
        "missingIconIndices": missing_icons,
    }

    runtime_path = out_dir / "runtime.json"
    runtime_path.write_text(json.dumps(runtime, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print("Generated real magic runtime:")
    print(f"  {runtime_path.relative_to(repo)} ({len(by_magic_id)} MagicInfo rows)")
    print(f"  {(out_dir / 'micon-atlas.webp').relative_to(repo)} ({len(icons)} icons)")
    if missing_icons:
        print(f"  WARNING: {len(missing_icons)} referenced MIcon frames could not be decoded")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Folder containing System.db and/or MIcon.Zl (recursive search is allowed)")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2], help=argparse.SUPPRESS)
    args = parser.parse_args()

    try:
        build(args.repo.resolve(), args.source)
    except (FileNotFoundError, ValueError, EOFError, UnicodeDecodeError) as exc:
        print("\nCould not build the real magic runtime:")
        print(f"  {exc}")
        print("Run again with --source pointing to the folder that contains System.db and MIcon.Zl.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
