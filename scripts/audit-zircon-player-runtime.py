#!/usr/bin/env python3
"""Audit ORIGINS-DxR player action/animation contracts against pinned Zircon.

This audit is intentionally source-faithful. It reports native MirAction values that
have no direct PlayerObject animation mapping instead of inventing one.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ZIRCON_COMMIT = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"
REQUESTED = [
    "Standing", "Walking", "Running", "Pushed", "Attack", "RangeAttack", "Spell",
    "Harvest", "Struck", "Die", "Dead", "Show", "Hide", "Mount", "Fishing", "Taming", "Idle",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def between(text: str, start: str, end: str) -> str:
    a = text.find(start)
    b = text.find(end, a + len(start)) if a >= 0 else -1
    if a < 0 or b < 0:
        return ""
    return text[a:b]


def require(label: str, text: str, tokens: list[str], failures: list[str]) -> None:
    for token in tokens:
        if token not in text:
            failures.append(f"{label}: missing {token}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--zircon", type=Path, default=Path("vendor/zircon"))
    p.add_argument("--json-output", type=Path, default=Path("artifacts/player-runtime/player-runtime-audit.json"))
    p.add_argument("--md-output", type=Path, default=Path("docs/generated/ORIGINS_DXR_PLAYER_RUNTIME_STATUS.md"))
    a = p.parse_args()

    repo = a.repo.resolve()
    zircon = (repo / a.zircon).resolve() if not a.zircon.is_absolute() else a.zircon.resolve()
    paths = {
        "enum": zircon / "LibraryCore/Enum.cs",
        "functions": zircon / "LibraryCore/Functions.cs",
        "player": zircon / "Client/Models/PlayerObject.cs",
        "user": zircon / "Client/Models/UserObject.cs",
        "mapobject": zircon / "Client/Models/MapObject.cs",
        "serverPlayer": zircon / "ServerLibrary/Models/PlayerObject.cs",
    }

    failures: list[str] = []
    text: dict[str, str] = {}
    for name, path in paths.items():
        try:
            text[name] = read(path)
        except Exception as exc:
            failures.append(f"{name}: cannot read {path}: {exc}")
            text[name] = ""

    enum_text = text["enum"]
    enum_block = between(enum_text, "public enum MirAction : byte", "public enum MirAnimation : byte")
    enum_actions = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*[^,]+)?\s*,?\s*$", enum_block, re.M)
    enum_actions = [x for x in enum_actions if x not in {"public", "enum"}]
    expected_enum = [
        "Standing", "Moving", "Pushed", "Attack", "RangeAttack", "Spell", "Harvest", "Struck",
        "Die", "Dead", "Show", "Hide", "Mount", "Mining", "Fishing", "Taming", "Idle",
    ]
    for action in expected_enum:
        if action not in enum_actions:
            failures.append(f"MirAction enum missing native value {action}")

    player = text["player"]
    user = text["user"]
    functions = text["functions"]
    mapobject = text["mapobject"]
    server_player = text["serverPlayer"]

    set_animation = between(player, "public override void SetAnimation(ObjectAction action)", "public sealed override void SetFrame")
    direct_cases = set(re.findall(r"case\s+MirAction\.([A-Za-z0-9_]+)\s*:", set_animation))

    direct_expected = {
        "Standing", "Moving", "Pushed", "Attack", "Mining", "Fishing", "Taming",
        "RangeAttack", "Spell", "Struck", "Die", "Dead", "Harvest",
    }
    if direct_cases != direct_expected:
        failures.append(f"PlayerObject.SetAnimation direct action set drifted: {sorted(direct_cases)}")

    require("PlayerObject action mapping", set_animation, [
        "animation = MirAnimation.Standing;",
        "animation = MirAnimation.Walking;",
        "animation = MirAnimation.Running;",
        "animation = MirAnimation.Pushed;",
        "Functions.GetAttackAnimation(Class, LibraryWeaponShape, type)",
        "case MirAction.RangeAttack:",
        "animation = MirAnimation.Combat1;",
        "Functions.GetMagicAnimation(type)",
        "animation = MirAnimation.Struck;",
        "animation = MirAnimation.HorseStruck;",
        "animation = MirAnimation.Die;",
        "animation = MirAnimation.Dead;",
        "animation = MirAnimation.Harvest;",
        "MirAnimation.FishingCast",
        "MirAnimation.FishingWait",
        "MirAnimation.FishingReel",
        "MirAnimation.TamingCast",
        "MirAnimation.TamingWait",
        "MirAnimation.HorseStanding",
        "MirAnimation.HorseWalking",
        "MirAnimation.HorseRunning",
    ], failures)

    require("PlayerObject libraries", player, [
        "Frames = new Dictionary<MirAnimation, Frame>(FrameSet.Players);",
        "public MirLibrary HairLibrary, HelmetLibrary;",
        "public MirLibrary WeaponLibrary1, WeaponLibrary2;",
        "public MirLibrary ShieldLibrary;",
        "public MirLibrary BodyLibrary;",
        "public MirLibrary HorseLibrary, HorseShapeLibrary, HorseShapeLibrary2;",
        "public int HairFrame => DrawFrame",
        "public int HelmetFrame => DrawFrame",
        "public int WeaponFrame => DrawFrame",
        "public int ShieldFrame => DrawFrame",
        "public int ArmourFrame => DrawFrame",
        "public int HorseFrame => DrawFrame",
        "switch (Class)",
        "case MirClass.Warrior:",
        "case MirClass.Wizard:",
        "case MirClass.Taoist:",
        "case MirClass.Assassin:",
    ], failures)

    require("PlayerObject directional layering", player, [
        "switch (Direction)",
        "case MirDirection.Up:",
        "case MirDirection.UpRight:",
        "case MirDirection.Right:",
        "case MirDirection.DownRight:",
        "case MirDirection.Down:",
        "case MirDirection.DownLeft:",
        "case MirDirection.Left:",
        "case MirDirection.UpLeft:",
        "WeaponLibrary1.Draw",
        "WeaponLibrary2.Draw",
        "ShieldLibrary.Draw",
        "BodyLibrary.Draw",
        "HelmetLibrary.Draw",
        "HairLibrary.Draw",
    ], failures)

    frame_changed = between(player, "public override void FrameIndexChanged()", "public override void Draw()")
    require("PlayerObject frame-synchronised effects", frame_changed, [
        "base.FrameIndexChanged();",
        "case MagicType.SeismicSlam:",
        "if (FrameIndex == 4)",
        "case MagicType.CrushingWave:",
        "new MirProjectile",
        "case MirAction.Fishing:",
        "if (FrameIndex != 1) return;",
        "case MirAction.Taming:",
        "if (FrameIndex != 5) return;",
        "case MagicType.OffensiveBlow:",
        "if (FrameIndex == 3)",
    ], failures)
    require("UserObject frame timing", user, [
        "public override void FrameIndexChanged()",
        "case MirAction.Moving:",
        "case MirAnimation.HorseWalking:",
        "if (FrameIndex == 1)",
        "if (FrameIndex == 4)",
        "case MirAnimation.HorseRunning:",
        "case MagicType.SeismicSlam:",
        "ShakeScreenCount = 20F;",
    ], failures)

    require("Attack animation authority", functions, [
        "public static MirAnimation GetAttackAnimation",
        "case MagicType.Slaying:",
        "case MagicType.HalfMoon:",
        "case MagicType.DragonRise:",
        "case MagicType.BladeStorm:",
        "case MirClass.Assassin:",
    ], failures)
    require("Magic animation authority", functions, [
        "public static MirAnimation GetMagicAnimation(MagicType m)",
        "return MirAnimation.Combat1;",
        "return MirAnimation.Combat2;",
        "return MirAnimation.Combat14;",
        "return MirAnimation.DragonRepulseStart;",
        "return MirAnimation.Combat15;",
        "throw new NotImplementedException();",
    ], failures)

    require("MapObject frame engine", mapobject, [
        "public int FrameIndex",
        "FrameIndexChanged();",
        "public MirAction CurrentAction;",
        "public MirAnimation CurrentAnimation;",
        "public Frame CurrentFrame;",
        "public DateTime FrameStart;",
        "public Dictionary<MirAnimation, Frame> Frames;",
        "UpdateFrame();",
    ], failures)

    require("UserObject native action dispatch", user, [
        "case MirAction.Mount:",
        "return;",
        "CEnvir.Enqueue(new C.Move",
        "CEnvir.Enqueue(new C.Attack",
        "CEnvir.Enqueue(new C.RangeAttack",
        "CEnvir.Enqueue(new C.Magic",
        "CEnvir.Enqueue(new C.FishingCast",
        "CEnvir.Enqueue(new C.Mining",
        "CEnvir.Enqueue(new C.Taming",
    ], failures)

    # Server runtime must remain the native authority for player execution. Avoid
    # overfitting this huge file to line numbers; validate the core class and action entry points.
    require("Server PlayerObject", server_player, [
        "public partial class PlayerObject : MapObject",
        "public override ObjectType Race => ObjectType.Player",
        "public void Walk(",
        "public void Attack(",
        "public void Magic(",
    ], failures)

    action_rows = [
        {"requested": "Standing", "mirAction": "Standing", "status": "DIRECT", "animation": "Standing; Stance/Creep/Horse/DragonRepulse/Channelling overrides by native state"},
        {"requested": "Walking", "mirAction": "Moving", "status": "DIRECT_VARIANT", "animation": "Walking; HorseWalking/Creep variants"},
        {"requested": "Running", "mirAction": "Moving", "status": "DIRECT_VARIANT", "animation": "Running when action.Extra[0] >= 2; HorseRunning when mounted"},
        {"requested": "Pushed", "mirAction": "Pushed", "status": "DIRECT", "animation": "Pushed"},
        {"requested": "Attack", "mirAction": "Attack", "status": "DIRECT", "animation": "Functions.GetAttackAnimation(class, weapon, magic)"},
        {"requested": "RangeAttack", "mirAction": "RangeAttack", "status": "DIRECT", "animation": "Combat1"},
        {"requested": "Spell", "mirAction": "Spell", "status": "DIRECT", "animation": "Functions.GetMagicAnimation(MagicType)"},
        {"requested": "Harvest", "mirAction": "Harvest", "status": "DIRECT", "animation": "Harvest"},
        {"requested": "Struck", "mirAction": "Struck", "status": "DIRECT", "animation": "Struck / HorseStruck"},
        {"requested": "Die", "mirAction": "Die", "status": "DIRECT", "animation": "Die"},
        {"requested": "Dead", "mirAction": "Dead", "status": "DIRECT", "animation": "Dead"},
        {"requested": "Show", "mirAction": "Show", "status": "NO_DIRECT_PLAYER_ANIMATION", "animation": None},
        {"requested": "Hide", "mirAction": "Hide", "status": "NO_DIRECT_PLAYER_ANIMATION", "animation": None},
        {"requested": "Mount", "mirAction": "Mount", "status": "STATE_DRIVEN", "animation": "UserObject AttemptAction returns; Horse state drives HorseStanding/Walking/Running/Struck"},
        {"requested": "Fishing", "mirAction": "Fishing", "status": "DIRECT", "animation": "FishingCast/FishingWait/FishingReel"},
        {"requested": "Taming", "mirAction": "Taming", "status": "DIRECT", "animation": "TamingCast/TamingWait"},
        {"requested": "Idle", "mirAction": "Idle", "status": "NO_DIRECT_PLAYER_ANIMATION", "animation": "PlayerObject DoNextAction falls back to Standing when no queued action"},
    ]

    native_unmapped = sorted(set(expected_enum) - direct_cases)
    result = {
        "schemaVersion": 1,
        "status": "PASS" if not failures else "FAIL",
        "zirconCommit": ZIRCON_COMMIT,
        "mirActionEnum": enum_actions,
        "directPlayerAnimationActions": sorted(direct_cases),
        "nativeActionsWithoutDirectPlayerAnimation": native_unmapped,
        "requestedAudit": action_rows,
        "equipmentLayers": ["Body", "Hair", "Helmet", "Weapon1", "Weapon2", "Shield", "Horse"],
        "frameAuthority": {
            "frameSet": "FrameSet.Players",
            "frameIndexChanged": True,
            "directionalLayering": True,
            "spellEffectsBoundToFrames": True,
        },
        "policy": {
            "crystalFrameTablesUsed": False,
            "missingAnimationsInvented": False,
            "sourceOfTruth": "pinned Zircon",
        },
        "failures": failures,
    }

    a.json_output.parent.mkdir(parents=True, exist_ok=True)
    a.json_output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# ORIGINS-DxR — native Zircon player runtime audit",
        "",
        f"- Gate: **{result['status']}**",
        f"- Zircon authority: `{ZIRCON_COMMIT}`",
        "- Frame source: `FrameSet.Players` + Zircon `MirAnimation`/`Functions`; no Crystal frame table.",
        "- Missing direct mappings are reported, not invented.",
        "",
        "| Requested behaviour | Native MirAction | Status | Native animation/behaviour |",
        "|---|---|---|---|",
    ]
    for row in action_rows:
        lines.append(f"| {row['requested']} | {row['mirAction']} | {row['status']} | {row['animation'] or 'none in PlayerObject.SetAnimation'} |")
    lines += [
        "",
        "## Player visual stack",
        "",
        "Verified native libraries/frames for Body, Hair, Helmet, Weapon1/Weapon2, Shield and Horse, including direction-dependent weapon/shield layering.",
        "",
        "## Frame-bound effects",
        "",
        "Verified `FrameIndexChanged()` gates for native effects including SeismicSlam (frame 4), CrushingWave (frame 4), OffensiveBlow (frame 3), TamingCast (frame 5) and Fishing (frame 1), plus user movement/horse sounds and SeismicSlam screen shake.",
        "",
        "## Native enum actions without direct PlayerObject animation",
        "",
        ", ".join(native_unmapped) if native_unmapped else "None",
        "",
        "`Mount` is state-driven through `Horse`; `Show`, `Hide` and `Idle` are not assigned a direct animation by pinned `PlayerObject.SetAnimation()`. ORIGINS-DxR does not fabricate replacements.",
    ]
    if failures:
        lines += ["", "## Failures", ""] + [f"- {x}" for x in failures]
    lines.append("")
    a.md_output.parent.mkdir(parents=True, exist_ok=True)
    a.md_output.write_text("\n".join(lines), encoding="utf-8")

    print(f"ORIGINS-DxR player runtime audit: {result['status']}; direct={len(direct_cases)}/{len(expected_enum)} MirAction values")
    for item in failures:
        print(f"FAIL: {item}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
