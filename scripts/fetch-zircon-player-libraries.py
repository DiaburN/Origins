#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import re
import shutil
import tempfile
import urllib.request
from pathlib import Path

PRIMARY_HOST = "https://mirfiles.com/resources/mir3/zircon/patch/"
MIRROR_HOST = "https://mirfiles.co.uk/resources/mir3/zircon/patch/"
BODY_LIBRARY_RE = re.compile(r"^(?:M|WM)_Hum(?:Ex\d+|Cx\d+|A(?:Ex\d+|Cx\d+)?)?$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "ORIGINS-DxR-ZirconAssetImporter/2.0"})
    with urllib.request.urlopen(request, timeout=300) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)


def patch_name(source_path: str) -> str:
    return source_path.replace("\\", "/").replace("/", "-") + ".gz"


def fetch_one(row: dict, output_root: Path) -> dict:
    library = row["libraryFile"]
    source_path = row["sourcePath"].replace("\\", "/")
    web_name = patch_name(source_path)
    destination = output_root / source_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    attempts: list[dict] = []

    with tempfile.TemporaryDirectory(prefix=f"origins-{library}-") as temp_dir:
        archive = Path(temp_dir) / web_name
        selected_url: str | None = None
        for host in (PRIMARY_HOST, MIRROR_HOST):
            url = host + web_name
            try:
                download(url, archive)
                size = archive.stat().st_size if archive.exists() else 0
                magic = archive.read_bytes()[:2] if size else b""
                if size <= 0:
                    raise RuntimeError("empty response")
                if magic != b"\x1f\x8b":
                    raise RuntimeError(f"not gzip (magic={magic.hex() or 'empty'})")
                selected_url = url
                attempts.append({"url": url, "success": True, "bytes": size, "error": None})
                break
            except Exception as exc:
                attempts.append({"url": url, "success": False, "error": f"{type(exc).__name__}: {exc}"})
                archive.unlink(missing_ok=True)

        if selected_url is None:
            return {
                "libraryFile": library,
                "sourcePath": source_path,
                "status": "MISSING_REMOTE",
                "attempts": attempts,
            }

        destination.unlink(missing_ok=True)
        try:
            with gzip.open(archive, "rb") as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
        except Exception as exc:
            destination.unlink(missing_ok=True)
            return {
                "libraryFile": library,
                "sourcePath": source_path,
                "status": "FAIL_DECOMPRESS",
                "patchUrl": selected_url,
                "attempts": attempts,
                "error": f"{type(exc).__name__}: {exc}",
            }

        return {
            "libraryFile": library,
            "sourcePath": source_path,
            "status": "READY",
            "patchUrl": selected_url,
            "attempts": attempts,
            "compressedBytes": archive.stat().st_size,
            "compressedSha256": sha256(archive),
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch selected pinned-Zircon player libraries from the official patch host.")
    parser.add_argument("--zircon-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--profile", choices=["body"], default=None)
    parser.add_argument("--library", action="append", default=[])
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    config = args.zircon_root / "Launcher" / "Config.cs"
    if not config.is_file():
        raise SystemExit(f"Missing pinned Zircon launcher config: {config}")
    if PRIMARY_HOST not in config.read_text(encoding="utf-8-sig"):
        raise SystemExit("Pinned Launcher/Config.cs no longer contains the expected MirFiles host.")

    contract = json.loads(args.contract.read_text(encoding="utf-8-sig"))
    rows = contract.get("playerLibraries", [])
    by_name = {row["libraryFile"]: row for row in rows}

    if args.profile == "body":
        selected = [row for row in rows if BODY_LIBRARY_RE.fullmatch(row.get("libraryFile", ""))]
    elif args.library:
        missing_names = [name for name in args.library if name not in by_name]
        if missing_names:
            raise SystemExit(f"Unknown contract player libraries: {missing_names}")
        selected = [by_name[name] for name in args.library]
    else:
        raise SystemExit("Use --profile body or at least one --library.")

    selected.sort(key=lambda row: row["libraryFile"])
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
        future_map = {pool.submit(fetch_one, row, args.output_root): row["libraryFile"] for row in selected}
        for future in concurrent.futures.as_completed(future_map):
            result = future.result()
            results.append(result)
            print(f"{result['libraryFile']}: {result['status']}", flush=True)

    results.sort(key=lambda row: row["libraryFile"])
    ready = sum(row["status"] == "READY" for row in results)
    missing = len(results) - ready
    payload = {
        "schema": "origins.zircon.player-library-fetch.v1",
        "zirconCommit": contract.get("zirconCommit"),
        "primaryPatchHost": PRIMARY_HOST,
        "approvedPatchHosts": [PRIMARY_HOST, MIRROR_HOST],
        "profile": args.profile or "explicit",
        "selected": len(results),
        "ready": ready,
        "missing": missing,
        "status": "PASS" if missing == 0 else ("PARTIAL" if ready else "FAIL"),
        "libraries": results,
    }
    args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("status", "selected", "ready", "missing")}, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
