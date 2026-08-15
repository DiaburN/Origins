#!/usr/bin/env python3
"""Download and extract only the Zircon .Zl images referenced by ui-source-spec.json."""
from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = "https://files.lomcn.co.uk/resources/mir3/zircon/patch"
UA = "Mozilla/5.0 (X11; Linux x86_64) ORIGINS-Zircon-UI-Reference"


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
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = response.read()
    target.write_bytes(gzip.decompress(payload))
    if not target.stat().st_size:
        raise RuntimeError(f"empty Zircon library: {target}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--spec", type=Path, required=True)
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
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
            # A missing peripheral library must remain visible in the build report;
            # never silently substitute another art source.
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

    (args.out / "ui-source-spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    (args.out / "asset-build.json").write_text(json.dumps(built, indent=2), encoding="utf-8")
    print("UI asset libraries processed:", len(built))


if __name__ == "__main__":
    main()
