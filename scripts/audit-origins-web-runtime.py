#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXPECTED_DIRECTIONS = [
    ("Up", 0),
    ("UpRight", 1),
    ("Right", 2),
    ("DownRight", 3),
    ("Down", 4),
    ("DownLeft", 5),
    ("Left", 6),
    ("UpLeft", 7),
]

EXPECTED_ACTIONS = [
    ("Standing", 0),
    ("Moving", 1),
    ("Pushed", 2),
    ("Attack", 3),
    ("RangeAttack", 4),
    ("Spell", 5),
    ("Harvest", 6),
    ("Struck", 7),
    ("Die", 8),
    ("Dead", 9),
    ("Show", 10),
    ("Hide", 11),
    ("Mount", 12),
    ("Mining", 13),
    ("Fishing", 14),
    ("Taming", 15),
    ("Idle", 16),
]

PINNED = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"


def enum_block(text: str, name: str) -> str:
    match = re.search(rf"public enum {re.escape(name)}\s*:[^{{]+\{{(.*?)\n\s*\}}", text, re.S)
    if not match:
        raise ValueError(f"missing enum {name}")
    return match.group(1)


def parse_csharp_enum(text: str, name: str) -> list[tuple[str, int]]:
    block = enum_block(text, name)
    block = re.sub(r"\[[^\]]+\]\s*", "", block)
    entries: list[tuple[str, int]] = []
    next_value = 0
    for raw in block.splitlines():
        line = raw.split("//", 1)[0].strip().rstrip(",")
        if not line:
            continue
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*([0-9]+))?$", line)
        if not match:
            continue
        key = match.group(1)
        if match.group(2) is not None:
            next_value = int(match.group(2))
        entries.append((key, next_value))
        next_value += 1
    return entries


def parse_js_object(text: str, constant: str) -> list[tuple[str, int]]:
    match = re.search(rf"export const {re.escape(constant)} = Object\.freeze\(\{{(.*?)\}}\);", text, re.S)
    if not match:
        raise ValueError(f"missing JS constant {constant}")
    entries: list[tuple[str, int]] = []
    for key, value in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([0-9]+)", match.group(1)):
        entries.append((key, int(value)))
    return entries


def check(condition: bool, name: str, details: str, results: list[dict]) -> None:
    results.append({"name": name, "pass": bool(condition), "details": details})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enum-source", required=True)
    parser.add_argument("--app-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    enum_source = Path(args.enum_source)
    app_root = Path(args.app_root)
    output = Path(args.output)

    results: list[dict] = []

    enum_text = enum_source.read_text(encoding="utf-8-sig")
    runtime_core = (app_root / "runtime-core.js").read_text(encoding="utf-8")
    main_js = (app_root / "main.js").read_text(encoding="utf-8")
    index_html = (app_root / "index.html").read_text(encoding="utf-8")

    try:
        source_directions = parse_csharp_enum(enum_text, "MirDirection")
        check(source_directions == EXPECTED_DIRECTIONS, "Pinned MirDirection source", str(source_directions), results)
    except Exception as exc:
        check(False, "Pinned MirDirection source", str(exc), results)
        source_directions = []

    try:
        source_actions = parse_csharp_enum(enum_text, "MirAction")
        check(source_actions == EXPECTED_ACTIONS, "Pinned MirAction source", str(source_actions), results)
    except Exception as exc:
        check(False, "Pinned MirAction source", str(exc), results)
        source_actions = []

    try:
        js_directions = parse_js_object(runtime_core, "MIR_DIRECTION")
        check(js_directions == source_directions == EXPECTED_DIRECTIONS, "Web MirDirection parity", str(js_directions), results)
    except Exception as exc:
        check(False, "Web MirDirection parity", str(exc), results)

    try:
        js_actions = parse_js_object(runtime_core, "MIR_ACTION")
        check(js_actions == source_actions == EXPECTED_ACTIONS, "Web MirAction parity", str(js_actions), results)
    except Exception as exc:
        check(False, "Web MirAction parity", str(exc), results)

    check(PINNED in runtime_core, "Pinned source commit declared", PINNED, results)
    check("FIXED_STEP_SECONDS = 1 / 60" in runtime_core, "Fixed simulation step", "1/60 second", results)
    check("PreviewPlayerObject" in runtime_core, "Preview PlayerObject model", "present", results)
    check("requestAnimationFrame" in main_js, "Browser render loop", "requestAnimationFrame", results)
    check("<canvas id=\"game-canvas\"" in index_html, "Canvas game surface", "present", results)
    check("data-vector=\"-1,-1\"" in index_html and "data-vector=\"1,1\"" in index_html, "Eight-way touch input", "diagonal controls present", results)

    active_text = "\n".join([runtime_core, main_js, index_html]).lower()
    check("crystal" not in active_text, "No Crystal runtime dependency", "no Crystal token in active Step 1 runtime", results)
    check("system.db" not in active_text and "users.db" not in active_text, "Browser does not open MirDB files", "no direct DB paths in runtime", results)
    check("new websocket" not in active_text, "No fake network authority in Step 1", "WebSocket deliberately absent until transport step", results)
    check("preview_local" in active_text, "Preview-only mode explicit", "PREVIEW_LOCAL visible in runtime", results)

    gate = "PASS" if all(item["pass"] for item in results) else "FAIL"
    payload = {
        "gate": gate,
        "zirconCommit": PINNED,
        "checks": results,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"ORIGINS web runtime audit: {gate}")
    for item in results:
        print(f"{'PASS' if item['pass'] else 'FAIL'}: {item['name']} — {item['details']}")
    return 0 if gate == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
