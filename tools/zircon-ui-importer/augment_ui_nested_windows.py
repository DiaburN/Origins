#!/usr/bin/env python3
"""Reconstruct source-defined Zircon DXWindow classes outside GameScene.

GameScene owns the 65 persistent/top-level in-game UI entries, but Zircon also
creates modal/transient DXWindow subclasses from those dialogs. This pass turns
`nestedWindowInventory` rows into renderable source specs and recursively expands
parameterless custom controls (for example KeyBindTree -> DXVScrollBar) without
inventing runtime list/data content.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_ui_source_spec import ROOT_PROPS, constructor_body, simple_assignments
from augment_ui_composites import (
    RENDER_TYPES,
    add_asset_refs,
    build_class_index,
    expand_instance,
    namespace_children,
    prepare_controls,
)

CTOR_RE = re.compile(r"\bpublic\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)")


def slug(name: str) -> str:
    first = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", first).lower()
    return re.sub(r"[^a-z0-9-]+", "-", value).strip("-")


def constructor_signature(text: str, class_name: str) -> str:
    for name, params in CTOR_RE.findall(text):
        if name == class_name:
            return " ".join(params.split())
    return ""


def root_properties(body: str) -> dict[str, str]:
    allowed = set(ROOT_PROPS) | {
        "Modal", "Title", "Text", "AllowResize", "AutomaticVisibility",
        "CustomSize", "HasFooter", "SlimFooter", "HasTitle", "HasTopBorder",
    }
    root = simple_assignments(body, allowed)
    title = re.search(r"\bTitleLabel\.Text\s*=\s*(.+?)\s*;", body, re.S)
    if title:
        root["Title"] = " ".join(title.group(1).split())
    close = re.search(r"\bCloseButton\.Visible\s*=\s*(true|false)\s*;", body)
    if close:
        root["CloseButtonVisible"] = close.group(1)
    return root


def category_for(source_path: str) -> str:
    if "/LoginScene.cs" in source_path: return "login"
    if "/SelectScene.cs" in source_path: return "character-select"
    if "GroupDialog.cs" in source_path: return "group"
    if "ConsignmentDialog.cs" in source_path: return "market"
    return "modal"


def runtime_contract_for(class_name: str) -> dict:
    """Describe only runtime dependencies explicitly present in Zircon source."""
    contracts = {
        "DXMessageBox": {
            "constructorRuntime": ["string message", "string caption", "DXMessageBoxButtons buttons = OK"],
            "sourceVariants": {
                "OK": ["OKButton"],
                "YesNo": ["YesButton", "NoButton"],
                "Cancel": ["CancelButton"],
            },
            "defaultReviewVariant": "OK",
            "sizeDependency": "Label.Size = (380, DXLabel.GetSize(message).Height); SetClientSize(Label.Size)",
            "inventRuntimeText": False,
        },
        "DXInputWindow": {
            "constructorRuntime": ["string message", "string caption"],
            "runtimeValue": "ValueTextBox user input",
            "sizeDependency": "Label height from runtime message; client height = Label.Size.Height + 30",
            "inventRuntimeText": False,
        },
        "DXItemAmountWindow": {
            "constructorRuntime": ["string caption", "ClientUserItem item"],
            "amountMax": "item.Count",
            "amountChange": "Math.Max(1, item.Count / 5)",
            "initialValue": 1,
            "itemCellData": "new[] { item }",
            "inventRuntimeItem": False,
        },
        "DXColourPicker": {
            "runtimeTexture": "RenderingPipelineManager.GetColourPaletteTexture()",
            "runtimeTarget": "DXColourControl Target",
            "rgbRange": [0, 255],
            "rgbChange": 5,
            "inventPaletteTexture": False,
        },
        "DXKeyBindWindow": {
            "runtimeRows": "CEnvir.KeyBinds grouped by BindInfo.Category",
            "sourceTreeScrollbar": True,
            "inventKeyBindings": False,
        },
    }
    return contracts.get(class_name, {})


def apply(spec: dict, zircon_root: Path) -> dict:
    inventory = spec.get("nestedWindowInventory", {}).get("windows", [])
    bases, sources, texts = build_class_index(zircon_root)
    nested: list[dict] = []
    skipped: list[dict] = []
    composite_children = 0
    composite_by_window: dict[str,int] = {}

    for row in inventory:
        class_name = row.get("sourceClass")
        source_path = row.get("sourcePath")
        path = sources.get(class_name)
        if not class_name or not source_path or not path:
            skipped.append({"sourceClass": class_name, "reason": "source missing"}); continue
        text = texts[path]
        body = constructor_body(text, class_name)
        if not body:
            skipped.append({"sourceClass": class_name, "reason": "constructor not found"}); continue

        controls = namespace_children(prepare_controls(body, class_name, text, bases, sources, texts), class_name)
        for control in controls:
            if control.setdefault("properties", {}).get("Parent") == class_name:
                control["properties"]["Parent"] = "this"

        additions=[]
        for control in list(controls):
            if control.get("sourceType") in RENDER_TYPES:
                continue
            children=expand_instance(control,bases,sources,texts,1,2)
            additions.extend(children)
        controls.extend(additions)
        composite_children += len(additions)
        composite_by_window[class_name]=len(additions)

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
            "root": root_properties(body),
            "controls": controls,
            "referenceCount": row.get("referenceCount", 0),
            "referencedFrom": row.get("referencedFrom", []),
            "runtimeDataInvented": False,
            "runtimeContract": runtime_contract_for(class_name),
            "renderStatus": "SOURCE_RECONSTRUCTED",
            "customCompositeChildren": len(additions),
        }
        add_asset_refs(spec, controls)
        nested.append(item)
        row.update(
            renderStatus="SOURCE_RECONSTRUCTED",
            controlCount=len(controls),
            nestedId=item["id"],
            customCompositeChildren=len(additions),
            runtimeContract=item["runtimeContract"],
        )

    spec["nestedWindows"] = nested
    report = spec.setdefault("nestedWindowInventory", {})
    report.update(
        reconstructedCount=len(nested), skipped=skipped,
        allPendingSourceReconstruction=bool(skipped),
        compositeChildrenAdded=composite_children,
        compositeChildrenByWindow=composite_by_window,
        runtimeContractsPreserved=True,
        runtimeValuesInvented=False,
    )

    expected = {
        'DXColourPicker','DXInputWindow','DXItemAmountWindow','DXKeyBindWindow','DXMessageBox',
        'GroupLFGInputWindow','MarketPlaceHistoryDialog','ActivationDialog','ChangePasswordDialog',
        'NewAccountDialog','NewCharacterDialog','RequestActivationKeyDialog',
        'RequestResetPasswordDialog','ResetPasswordDialog','SelectDialog',
    }
    actual={row.get('sourceClass') for row in inventory}
    if actual != expected:
        raise RuntimeError(f"Nested Zircon window inventory changed: {sorted(actual)}")
    if skipped or len(nested) != len(expected):
        raise RuntimeError(f"Nested Zircon source reconstruction incomplete: nested={len(nested)} skipped={skipped}")
    keybind=next((w for w in nested if w['sourceClass']=='DXKeyBindWindow'),None)
    if not keybind or not any(c.get('type')=='DXVScrollBar' for c in keybind.get('controls',[])):
        raise RuntimeError('DXKeyBindWindow KeyBindTree scrollbar composite was not expanded')
    message=next((w for w in nested if w['sourceClass']=='DXMessageBox'),None)
    if message.get('runtimeContract',{}).get('sourceVariants',{}).get('YesNo') != ['YesButton','NoButton']:
        raise RuntimeError('DXMessageBox source variant contract lost')
    amount=next((w for w in nested if w['sourceClass']=='DXItemAmountWindow'),None)
    if amount.get('runtimeContract',{}).get('amountMax') != 'item.Count':
        raise RuntimeError('DXItemAmountWindow runtime item.Count contract lost')
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report=apply(spec,args.zircon_root)
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Nested/transient windows source-reconstructed:", report.get('reconstructedCount',0))
    print("Nested custom composite children added:", report.get('compositeChildrenAdded',0))
    print("Nested runtime contracts preserved:", report.get('runtimeContractsPreserved'))
    print("Nested/transient windows skipped:", len(report.get('skipped',[])))
    for item in spec.get('nestedWindows',[]):
        print("  RECONSTRUCTED", item["sourceClass"], "controls=", len(item["controls"]), "customChildren=",item.get('customCompositeChildren',0))


if __name__ == "__main__":
    main()
