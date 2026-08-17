#!/usr/bin/env python3
"""Reconstruct source-defined Zircon DXWindow classes outside GameScene.

GameScene owns the 65 persistent/top-level in-game UI entries, but Zircon also
creates modal/transient DXWindow subclasses from those dialogs. This pass turns
`nestedWindowInventory` rows into renderable source specs without inventing
runtime list/data content.

The result is stored separately as `nestedWindows`; `windowCount` remains the
canonical 65 GameScene entries so existing runtime contracts do not change.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_ui_source_spec import ROOT_PROPS, constructor_body, simple_assignments
from augment_ui_composites import (
    add_asset_refs,
    build_class_index,
    namespace_children,
    prepare_controls,
)

CTOR_RE = re.compile(r"\bpublic\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)")


def slug(name: str) -> str:
    value = re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()
    return re.sub(r"[^a-z0-9-]+", "-", value).strip("-")


def constructor_signature(text: str, class_name: str) -> str:
    for name, params in CTOR_RE.findall(text):
        if name == class_name:
            return " ".join(params.split())
    return ""


def root_properties(body: str) -> dict[str, str]:
    # simple_assignments also captures SetClientSize(...) as ClientSize.
    allowed = set(ROOT_PROPS) | {
        "Modal", "Title", "Text", "AllowResize", "AutomaticVisibility",
        "CustomSize", "HasFooter", "SlimFooter", "HasTitle", "HasTopBorder",
    }
    return simple_assignments(body, allowed)


def category_for(source_path: str) -> str:
    if "/LoginScene.cs" in source_path:
        return "login"
    if "/SelectScene.cs" in source_path:
        return "character-select"
    if "GroupDialog.cs" in source_path:
        return "group"
    if "ConsignmentDialog.cs" in source_path:
        return "market"
    return "modal"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    inventory = spec.get("nestedWindowInventory", {}).get("windows", [])
    bases, sources, texts = build_class_index(args.zircon_root)

    nested: list[dict] = []
    skipped: list[dict] = []
    for row in inventory:
        class_name = row.get("sourceClass")
        source_path = row.get("sourcePath")
        path = sources.get(class_name)
        if not class_name or not source_path or not path:
            skipped.append({"sourceClass": class_name, "reason": "source missing"})
            continue

        text = texts[path]
        body = constructor_body(text, class_name)
        if not body:
            skipped.append({"sourceClass": class_name, "reason": "constructor not found"})
            continue

        controls = prepare_controls(body, class_name, text, bases, sources, texts)
        controls = namespace_children(controls, "this")
        # namespace_children() uses the supplied parent name for Parent=this.
        # For a top-level window, restore those children to the root sentinel.
        for control in controls:
            props = control.setdefault("properties", {})
            if props.get("Parent") == "this":
                props["Parent"] = "this"
            elif props.get("Parent") == "this":
                props["Parent"] = "this"

        root = root_properties(body)
        item = {
            "id": f"nested-{slug(class_name)}",
            "field": class_name,
            "class": class_name,
            "sourceClass": class_name,
            "baseClass": bases.get(class_name, "DXWindow"),
            "sourcePath": source_path,
            "constructorSignature": constructor_signature(text, class_name),
            "defaultVisible": False,
            "nested": True,
            "category": category_for(source_path),
            "root": root,
            "controls": controls,
            "referenceCount": row.get("referenceCount", 0),
            "referencedFrom": row.get("referencedFrom", []),
            "runtimeDataInvented": False,
            "renderStatus": "SOURCE_RECONSTRUCTED",
        }
        add_asset_refs(spec, controls)
        nested.append(item)
        row["renderStatus"] = "SOURCE_RECONSTRUCTED"
        row["controlCount"] = len(controls)
        row["nestedId"] = item["id"]

    spec["nestedWindows"] = nested
    nested_report = spec.setdefault("nestedWindowInventory", {})
    nested_report["reconstructedCount"] = len(nested)
    nested_report["skipped"] = skipped
    nested_report["allPendingSourceReconstruction"] = bool(skipped)

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Nested/transient windows source-reconstructed:", len(nested))
    print("Nested/transient windows skipped:", len(skipped))
    for item in nested:
        print("  RECONSTRUCTED", item["sourceClass"], "controls=", len(item["controls"]), "ctor=", item["constructorSignature"] or "()")
    for item in skipped:
        print("  SKIPPED", item)


if __name__ == "__main__":
    main()
