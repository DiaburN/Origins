#!/usr/bin/env python3
"""Strict gate for GuildDialog's deterministic GuildMemberRow structure."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


LABELS = ("NameLabel", "RankLabel", "TotalLabel", "DailyLabel", "OnlineLabel")
POSITIONS = {
    "NameLabel": "new Point(10, 2)",
    "RankLabel": "new Point(110, 2)",
    "TotalLabel": "new Point(210, 2)",
    "DailyLabel": "new Point(310, 2)",
    "OnlineLabel": "new Point(400, 2)",
}


def props(control: dict | None) -> dict:
    return (control or {}).get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    guild = next((w for w in spec.get("windows", []) if w.get("field") == "GuildBox"), None)
    if guild is None:
        raise SystemExit("GuildBox missing")
    contract = guild.get("deterministicGuildMemberRows") or {}
    if contract.get("headerRows") != 1 or contract.get("memberRows") != 17:
        raise SystemExit(f"Guild member row count drifted: {contract}")
    if contract.get("rowSize") != [402, 20] or contract.get("rowStep") != 23:
        raise SystemExit(f"Guild member row geometry contract drifted: {contract}")
    if contract.get("regularRowsVisible") is not False or contract.get("memberInfoInvented") is not False:
        raise SystemExit(f"Guild member neutral runtime contract broken: {contract}")
    if contract.get("generatedControls") != 108:
        raise SystemExit(f"Guild member composite size drifted: {contract}")
    if contract.get("replacedIncompleteCompositeControls") != 1 or contract.get("netControlsAdded") != 107:
        raise SystemExit(f"Guild member base-composite reconciliation drifted: {contract}")

    by = {control.get("name"): control for control in guild.get("controls", [])}
    header = by.get("GuildMemberHeaderSource")
    if header is None:
        raise SystemExit("Guild member source header missing")
    if props(header).get("Location") != "new Point(7, 9)" or props(header).get("Size") != "new Size(402, 20)":
        raise SystemExit(f"Guild member header geometry drifted: {props(header)}")
    if props(header).get("Visible") != "true" or props(header).get("DrawTexture") != "false":
        raise SystemExit(f"Guild member header initial state drifted: {props(header)}")
    for suffix in LABELS:
        label = by.get(f"GuildMemberHeaderSource{suffix}")
        if label is None:
            raise SystemExit(f"Guild member header label missing: {suffix}")
        if props(label).get("Location") != POSITIONS[suffix]:
            raise SystemExit(f"Guild member header label geometry drifted: {suffix} -> {props(label)}")
        if not str(label.get("resolvedText") or "").strip():
            raise SystemExit(f"Guild member source header label text unresolved: {suffix}")

    for i in range(17):
        name = f"GuildMemberRowSource{i + 1:02d}"
        row = by.get(name)
        if row is None:
            raise SystemExit(f"Guild member deterministic row missing: {name}")
        expected_location = f"new Point(16, {34 + i * 23})"
        if props(row).get("Location") != expected_location or props(row).get("Size") != "new Size(402, 20)":
            raise SystemExit(f"Guild member row geometry drifted: {name} -> {props(row)}")
        if props(row).get("Visible") != "false" or props(row).get("DrawTexture") != "true":
            raise SystemExit(f"Guild member neutral row state drifted: {name} -> {props(row)}")
        if "null in neutral reference" not in str(props(row).get("RuntimeMemberInfo") or ""):
            raise SystemExit(f"Guild member runtime boundary missing: {name}")
        for suffix in LABELS:
            label = by.get(f"{name}{suffix}")
            if label is None:
                raise SystemExit(f"Guild member row child missing: {name}{suffix}")
            if props(label).get("Location") != POSITIONS[suffix]:
                raise SystemExit(f"Guild member row label geometry drifted: {name}{suffix}")
            if label.get("resolvedText") not in ("", None):
                raise SystemExit(f"Fabricated guild member data leaked into {name}{suffix}")

    # The original incomplete helper-composite header must not survive beside
    # the full source composite, otherwise desktop renders a duplicate header.
    stale = [
        control.get("name") for control in guild.get("controls", [])
        if control.get("sourceType") == "GuildMemberRow"
        and control.get("compositeChild")
        and props(control).get("Parent") == "MemberTab"
    ]
    if stale:
        raise SystemExit(f"Stale incomplete GuildMemberRow composite remains: {stale}")

    spec["guildMemberRowAudit"] = {
        "passed": True,
        "headerRows": 1,
        "memberRows": 17,
        "sourceControls": 108,
        "netControlsAdded": 107,
        "runtimeMembersInvented": False,
        "runtimeRanksInvented": False,
        "runtimeOnlineStateInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Guild member row audit: PASS (1 header + 17 neutral rows, 108 controls)")


if __name__ == "__main__":
    main()
