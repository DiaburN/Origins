#!/usr/bin/env python3
"""Download and extract only the Zircon .Zl images referenced by ui-source-spec.json."""
from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

BASE = "https://files.lomcn.co.uk/resources/mir3/zircon/patch"
UA = "Mozilla/5.0 (X11; Linux x86_64) ORIGINS-Zircon-UI-Reference"

# Reusable controls draw some chrome in their control classes instead of
# declaring LibraryFile/Index in each GameScene view.
CONTROL_ASSET_REFS: dict[str, set[int]] = {
    "GameInter": {
        161, 162,
        795,
        1010, 1011,
        4740, 4741, 4742, 4743, 4745, 4746,
    },
    "Interface": {
        16, 17, 18,
        41, 42, 43,
        44, 45, 46,
        53, 54, 55,
        56, 57, 58,
        59, 60, 61, 62,
        206,
        241, 242, 243, 245,
    },
}


def ranges(values: list[int]) -> str:
    if not values:
        return ""
    values = sorted(set(values))
    out: list[str] = []
    start = prev = values[0]
    for value in values[1:]:
        if value == prev + 1:
            prev = value
            continue
        out.append(str(start) if start == prev else f"{start}-{prev}")
        start = prev = value
    out.append(str(start) if start == prev else f"{start}-{prev}")
    return ",".join(out)


def download(remote: str, target: Path) -> None:
    if target.exists() and target.stat().st_size:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BASE}/{remote}.gz"
    print("DOWNLOAD", url)
    payload = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as response:
            payload = response.read()
    except Exception as first_error:
        print("urllib failed; trying curl:", first_error)
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            subprocess.run([
                "curl", "-fL", "--retry", "5", "--retry-delay", "3",
                "-A", UA, url, "-o", str(tmp_path)
            ], check=True)
            payload = tmp_path.read_bytes()
        finally:
            tmp_path.unlink(missing_ok=True)
    if not payload:
        raise RuntimeError(f"empty download: {url}")
    target.write_bytes(gzip.decompress(payload))
    if not target.stat().st_size:
        raise RuntimeError(f"empty Zircon library: {target}")


def merge_control_asset_refs(spec: dict) -> None:
    refs = spec.setdefault("assetRefs", {})
    for library, ids in CONTROL_ASSET_REFS.items():
        merged = {int(value) for value in refs.get(library, [])}
        merged.update(ids)
        refs[library] = sorted(merged)


def collect_asset_sizes(output: Path) -> dict[str, dict[str, list[int]]]:
    """Read extractor manifests and embed dimensions into the UI spec.

    The browser can then resolve `Size.Width`, image-backed control sizes and
    root window dimensions without waiting for DOM image load events.
    """
    result: dict[str, dict[str, list[int]]] = {}
    assets_root = output / "assets"
    if not assets_root.exists():
        return result
    for library_dir in assets_root.iterdir():
        if not library_dir.is_dir():
            continue
        manifest_path = library_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        sizes: dict[str, list[int]] = {}
        for index, info in manifest.get("images", {}).items():
            size = info.get("size")
            if isinstance(size, list) and len(size) == 2:
                sizes[str(index)] = [int(size[0]), int(size[1])]
        if sizes:
            result[library_dir.name] = sizes
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--spec", type=Path, required=True)
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    merge_control_asset_refs(spec)
    extractor = Path(__file__).with_name("extract_zl_assets.py")
    args.out.mkdir(parents=True, exist_ok=True)

    built: dict[str, dict] = {}
    for enum_name, ids in spec.get("assetRefs", {}).items():
        source_rel = spec.get("libraries", {}).get(enum_name)
        if not source_rel:
            print("SKIP no Libraries.cs mapping for", enum_name)
            continue
        filename = Path(source_rel.replace("\\", "/")).name
        target = args.source_dir / filename
        remote = "Data-" + filename
        try:
            download(remote, target)
        except Exception as exc:
            print("MISSING", enum_name, filename, exc)
            built[enum_name] = {"file": filename, "missing": True, "ids": ids}
            continue

        output = args.out / "assets" / enum_name
        spec_ids = ranges([int(x) for x in ids])
        cmd = [sys.executable, str(extractor), str(target), str(output)]
        if spec_ids:
            cmd += ["--ids", spec_ids]
        print("EXTRACT", enum_name, spec_ids)
        subprocess.run(cmd, check=True)
        built[enum_name] = {"file": filename, "missing": False, "ids": ids}

    spec["assetSizes"] = collect_asset_sizes(args.out)
    (args.out / "ui-source-spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    (args.out / "asset-build.json").write_text(json.dumps(built, indent=2), encoding="utf-8")
    print("UI asset libraries processed:", len(built))
    print("UI libraries with embedded asset sizes:", len(spec["assetSizes"]))


if __name__ == "__main__":
    main()
