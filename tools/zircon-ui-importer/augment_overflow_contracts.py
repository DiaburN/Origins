#!/usr/bin/env python3
"""Classify the last source-correct geometry overflows.

These are not generic exceptions. Each entry is tied to a concrete Zircon
constructor/runtime method so the final audit can fail on any other overflow.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def control(window: dict, *, name: str | None = None, source_name: str | None = None) -> dict:
    for item in window.get("controls", []):
        if name is not None and item.get("name") == name:
            return item
        if source_name is not None and item.get("sourceName") == source_name:
            return item
    raise SystemExit(f"{window.get('field') or window.get('sourceClass')}: control missing: {name or source_name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    by_field = {item.get("field"): item for item in spec.get("windows", [])}

    # NPCGoodsDialog constructor intentionally places GuildCheckBox at x=200.
    # NewGoods(...) later moves it to x=120 and decides visibility from currency.
    goods = by_field["NPCGoodsBox"]
    guild = control(goods, name="GuildCheckBox")
    guild["overflowContract"] = {
        "kind": "SOURCE_RUNTIME_RELOCATION",
        "reason": "constructor x=200; NewGoods moves x=120 and sets Visible from Currency.Type",
        "runtimeDataInvented": False,
    }

    # NPCRollDialog has no constructor Size. Setup(type, result, autoRoll) chooses
    # 65x65 (Die) or 180x210 (Yut). MiniGames images use source offsets.
    roll = by_field["NPCRollBox"]
    animation = control(roll, name="_animation")
    animation["overflowContract"] = {
        "kind": "RUNTIME_SIZED_MINIGAME",
        "reason": "Setup runtime chooses Die 65x65 or Yut 180x210; UseOffSet=true",
        "runtimeDataInvented": False,
    }
    roll["runtimeSizeContract"] = {
        "initial": "DXControl default/unspecified until Setup",
        "variants": {"Die": [65, 65], "Yut": [180, 210]},
        "runtimeTypeInvented": False,
    }

    # Timer egg frames deliberately use offsets and are clipped by the parent
    # DXControl. The constructor is deterministic and remains visible.
    timer = by_field["TimerBox"]
    egg = control(timer, name="_eggTimer")
    egg["overflowContract"] = {
        "kind": "SOURCE_OFFSET_PARENT_CLIP",
        "reason": "DXAnimatedControl Index=960, UseOffSet=true, parent TimerDialog 120x100",
        "runtimeDataInvented": False,
    }

    # FishingCatch MovingPointer starts as Interface #0, but CatchBar.BeforeDraw
    # immediately hides it while there is no live Cast+FishFound state. The
    # neutral reference should project that first-frame source state.
    fishing = by_field["FishingCatchBox"]
    moving = control(fishing, name="MovingPointer")
    moving["sourceNeutralVisible"] = False
    moving["overflowContract"] = {
        "kind": "SOURCE_BEFORE_DRAW_HIDDEN",
        "reason": "CatchBar.BeforeDraw hides MovingPointer unless FishingState.Cast && FishFound",
        "runtimeDataInvented": False,
    }

    # GroupLFGInputWindow: Label.Size = new Size(300, DXLabel.GetHeight(...).Height).
    # The current resolver cannot evaluate the dynamic height but the width is
    # fully deterministic and must never fall back to text auto-width.
    group = next((item for item in spec.get("nestedWindows", []) if item.get("sourceClass") == "GroupLFGInputWindow"), None)
    if not group:
        raise SystemExit("GroupLFGInputWindow missing")
    label = control(group, source_name="Label")
    label["sourceResolvedWidth"] = 300
    label["overflowContract"] = {
        "kind": "PARTIAL_DYNAMIC_SIZE",
        "reason": "source Size width=300; height=DXLabel.GetHeight(Label,300).Height",
        "runtimeDataInvented": False,
    }
    group.setdefault("root", {})["sourceResolvedClientWidth"] = 300
    group["dynamicHeightContract"] = "SetClientSize(new Size(300, 60 + Label.Size.Height))"

    contracts = [
        ("NPCGoodsBox", "GuildCheckBox", "SOURCE_RUNTIME_RELOCATION"),
        ("NPCRollBox", "_animation", "RUNTIME_SIZED_MINIGAME"),
        ("TimerBox", "_eggTimer", "SOURCE_OFFSET_PARENT_CLIP"),
        ("FishingCatchBox", "MovingPointer", "SOURCE_BEFORE_DRAW_HIDDEN"),
        ("GroupLFGInputWindow", label.get("name"), "PARTIAL_DYNAMIC_SIZE"),
    ]
    spec["overflowContractPass"] = {
        "contractCount": len(contracts),
        "contracts": contracts,
        "policy": "all other visible top-level overflows must fail final CI",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Overflow contracts promoted:", len(contracts))


if __name__ == "__main__":
    main()
