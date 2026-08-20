#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

PRIMARY_HOST = "https://mirfiles.com/resources/mir3/zircon/patch/"
MIRROR_HOST = "https://mirfiles.co.uk/resources/mir3/zircon/patch/"
TARGETS = (
    ("M_Hum", "M-Hum.Zl", "Data-M-Hum.Zl.gz"),
    ("WM_Hum", "WM-Hum.Zl", "Data-WM-Hum.Zl.gz"),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_report(path: Path, *, status: str, libraries: list[dict], current: str | None = None,
                 error: str | None = None, attempts: list[dict] | None = None) -> None:
    payload = {
        "schema": "origins.zircon.base-human-fetch.v1",
        "status": status,
        "primaryPatchHost": PRIMARY_HOST,
        "approvedPatchHosts": [PRIMARY_HOST, MIRROR_HOST],
        "patchHostSource": "vendor/zircon/Launcher/Config.cs",
        "currentLibrary": current,
        "error": error,
        "attempts": attempts or [],
        "libraries": libraries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ORIGINS-DxR-ZirconAssetImporter/1.0"},
    )
    with urllib.request.urlopen(request, timeout=300) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zircon-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    libraries: list[dict] = []
    write_report(args.report, status="STARTED", libraries=libraries)

    try:
        config = args.zircon_root / "Launcher" / "Config.cs"
        if not config.is_file():
            raise FileNotFoundError(f"Missing pinned Zircon Launcher/Config.cs: {config}")
        config_text = config.read_text(encoding="utf-8-sig")
        if PRIMARY_HOST not in config_text:
            raise RuntimeError(f"Pinned Launcher/Config.cs does not contain expected host: {PRIMARY_HOST}")

        data_root = args.output_root / "Data"
        data_root.mkdir(parents=True, exist_ok=True)

        for library, filename, web_name in TARGETS:
            attempts: list[dict] = []
            selected_url: str | None = None
            with tempfile.TemporaryDirectory(prefix="origins-zircon-") as temp_dir:
                archive = Path(temp_dir) / web_name

                for host in (PRIMARY_HOST, MIRROR_HOST):
                    url = host + web_name
                    try:
                        print(f"Downloading {library} from {url}", flush=True)
                        download(url, archive)
                        size = archive.stat().st_size if archive.exists() else 0
                        with archive.open("rb") as handle:
                            magic = handle.read(2)
                        if size <= 0:
                            raise RuntimeError("empty response")
                        if magic != b"\x1f\x8b":
                            raise RuntimeError(f"not gzip (magic={magic.hex() or 'empty'})")
                        selected_url = url
                        attempts.append({"url": url, "success": True, "bytes": size, "error": None})
                        break
                    except Exception as exc:  # keep exact host diagnostics
                        attempts.append({"url": url, "success": False, "error": f"{type(exc).__name__}: {exc}"})
                        archive.unlink(missing_ok=True)

                if selected_url is None:
                    write_report(
                        args.report,
                        status="FAIL_DOWNLOAD",
                        libraries=libraries,
                        current=library,
                        error=f"No approved MirFiles host returned a valid gzip for {web_name}",
                        attempts=attempts,
                    )
                    return 2

                destination = data_root / filename
                destination.unlink(missing_ok=True)
                try:
                    with gzip.open(archive, "rb") as source, destination.open("wb") as output:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
                except Exception as exc:
                    write_report(
                        args.report,
                        status="FAIL_DECOMPRESS",
                        libraries=libraries,
                        current=library,
                        error=f"{type(exc).__name__}: {exc}",
                        attempts=attempts,
                    )
                    return 3

                if destination.stat().st_size <= 0:
                    raise RuntimeError(f"Decompressed Zircon library is empty: {destination}")

                libraries.append({
                    "libraryFile": library,
                    "sourcePath": f"Data/{filename}",
                    "patchUrl": selected_url,
                    "attempts": attempts,
                    "compressedBytes": archive.stat().st_size,
                    "compressedSha256": sha256(archive),
                    "bytes": destination.stat().st_size,
                    "sha256": sha256(destination),
                })
                write_report(args.report, status="IN_PROGRESS", libraries=libraries, current=library)

        write_report(args.report, status="PASS", libraries=libraries)
        print(args.report.read_text(encoding="utf-8"), flush=True)
        return 0

    except Exception as exc:
        write_report(
            args.report,
            status="FAIL_SCRIPT",
            libraries=libraries,
            error=f"{type(exc).__name__}: {exc}",
        )
        print(args.report.read_text(encoding="utf-8"), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
