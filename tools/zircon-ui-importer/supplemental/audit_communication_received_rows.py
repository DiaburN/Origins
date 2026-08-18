#!/usr/bin/env python3
"""Strict gate for CommunicationDialog's five deterministic received rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def props(control: dict | None) -> dict:
    return (control or {}).get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "CommunicationBox"), None)
    if window is None:
        raise SystemExit("CommunicationBox missing")
    contract = window.get("deterministicCommunicationReceivedRows") or {}
    expected = {
        "passed": True,
        "rows": 5,
        "controlsAdded": 25,
        "rowSize": [236, 49],
        "rowStep": 49,
        "neutralVisible": False,
        "runtimeMailInvented": False,
        "runtimeSenderInvented": False,
        "runtimeSubjectInvented": False,
        "runtimeDateInvented": False,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise SystemExit(f"Communication row contract drifted: {key}={contract.get(key)!r}, expected {value!r}")

    by = {str(control.get("name") or ""): control for control in window.get("controls", [])}
    for i in range(5):
        row_name = f"CommunicationReceivedRowSource{i + 1:02d}"
        row = by.get(row_name)
        if row is None or row.get("sourceType") != "CommunicationReceivedRow":
            raise SystemExit(f"Communication received row missing: {row_name}")
        p = props(row)
        if p.get("Location") != f"new Point(18, {43 + 49 * i})" or p.get("Size") != "new Size(236, 49)":
            raise SystemExit(f"Communication row geometry drifted: {row_name} -> {p}")
        if p.get("Visible") != "false" or p.get("DrawTexture") != "true":
            raise SystemExit(f"Communication neutral row state drifted: {row_name} -> {p}")
        if "null in neutral reference" not in str(p.get("RuntimeMail") or ""):
            raise SystemExit(f"Communication runtime Mail boundary missing: {row_name}")
        icon = by.get(f"{row_name}Icon")
        if props(icon).get("Index") != "3680" or props(icon).get("LibraryFile") != "LibraryFile.GameInter":
            raise SystemExit(f"Communication received icon source asset drifted: {row_name}")
        for suffix in ("SubjectLabel", "SenderLabel", "DateLabel"):
            label = by.get(f"{row_name}{suffix}")
            if label is None or label.get("resolvedText") not in ("", None):
                raise SystemExit(f"Fabricated Communication mail data leaked: {row_name}{suffix}")

    generated = [
        control for control in window.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-communication-mail:")
    ]
    if len(generated) != 25:
        raise SystemExit(f"Communication generated row controls drifted: {len(generated)}")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("Communication received rows introduced runtime payloads")
    if 3680 not in {int(value) for value in spec.get("assetRefs", {}).get("GameInter", [])}:
        raise SystemExit("Communication received-row GameInter 3680 asset was not promoted")

    spec["communicationReceivedRowAudit"] = {
        "passed": True,
        "rows": 5,
        "deterministicControls": 25,
        "runtimeMailInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Communication received-row audit: PASS (5 rows / 25 controls, no mail data)")


if __name__ == "__main__":
    main()
