#!/usr/bin/env python3
"""Audit the pinned Zircon player runtime without inventing ORIGINS behaviour."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ZIRCON_COMMIT = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"
EXPECTED_ACTIONS = [
    "Standing", "Moving", "Pushed", "Attack", "RangeAttack", "Spell", "Harvest",
    "Struck", "Die", "Dead", "Show", "Hide", "Mount", "Mining", "Fishing",
    "Taming", "Idle",
]
DIRECT_PLAYER_ACTIONS = {
    "Standing", "Moving", "Pushed", "Attack", "RangeAttack", "Spell", "Harvest",
    "Struck", "Die", "Dead", "Mining", "Fishing", "Taming",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def between(text: str, start: str, end: str) -> str:
    a = text.find(start)
    b = text.find(end, a + len(start)) if a >= 0 else -1
    return text[a:b] if a >= 0 and b >= 0 else ""


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
    sources = {
        "enum": zircon / "LibraryCore/Enum.cs",
        "functions": zircon / "LibraryCore/Functions.cs",
        "player": zircon / "Client/Models/PlayerObject.cs",
        "user": zircon / "Client/Models/UserObject.cs",
        "map": zircon / "Client/Models/MapObject.cs",
        "serverPlayer": zircon / "ServerLibrary/Models/PlayerObject.cs",
        "connection": zircon / "ServerLibrary/Envir/SConnection.cs",
    }

    failures: list[str] = []
    text: dict[str, str] = {}
    for name, path in sources.items():
        try:
            text[name] = read(path)
        except Exception as exc:
            text[name] = ""
            failures.append(f"{name}: cannot read {path}: {exc}")

    enum_block = between(text["enum"], "public enum MirAction : byte", "public enum MirAnimation : byte")
    enum_actions = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*[^,]+)?\s*,?\s*$", enum_block, re.M)
    for action in EXPECTED_ACTIONS:
        if action not in enum_actions:
            failures.append(f"MirAction enum missing {action}")

    set_animation = between(
        text["player"],
        "public override void SetAnimation(ObjectAction action)",
        "public sealed override void SetFrame",
    )
    direct_cases = set(re.findall(r"case\s+MirAction\.([A-Za-z0-9_]+)\s*:", set_animation))
    if direct_cases != DIRECT_PLAYER_ACTIONS:
        failures.append(
            "PlayerObject.SetAnimation direct action set drifted: "
            + ", ".join(sorted(direct_cases))
        )

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

    require("Player visual stack", text["player"], [
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
        "case MirClass.Warrior:",
        "case MirClass.Wizard:",
        "case MirClass.Taoist:",
        "case MirClass.Assassin:",
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

    player_frame_changed = between(
        text["player"], "public override void FrameIndexChanged()", "public override void Draw()"
    )
    require("Player FrameIndexChanged", player_frame_changed, [
        "base.FrameIndexChanged();",
        "case MagicType.SeismicSlam:",
        "case MagicType.CrushingWave:",
        "new MirProjectile",
        "case MirAction.Fishing:",
        "if (FrameIndex != 1) return;",
        "case MirAction.Taming:",
        "if (FrameIndex != 5) return;",
        "case MagicType.OffensiveBlow:",
        "if (FrameIndex == 3)",
    ], failures)

    require("User FrameIndexChanged", text["user"], [
        "public override void FrameIndexChanged()",
        "case MirAction.Moving:",
        "case MirAnimation.HorseWalking:",
        "case MirAnimation.HorseRunning:",
        "case MagicType.SeismicSlam:",
        "ShakeScreenCount = 20F;",
    ], failures)

    require("Attack animation authority", text["functions"], [
        "public static MirAnimation GetAttackAnimation",
        "case MagicType.Slaying:",
        "case MagicType.HalfMoon:",
        "case MagicType.DragonRise:",
        "case MagicType.BladeStorm:",
        "case MirClass.Assassin:",
    ], failures)
    require("Magic animation authority", text["functions"], [
        "public static MirAnimation GetMagicAnimation(MagicType m)",
        "return MirAnimation.Combat1;",
        "return MirAnimation.Combat2;",
        "return MirAnimation.Combat14;",
        "return MirAnimation.DragonRepulseStart;",
        "return MirAnimation.Combat15;",
        "throw new NotImplementedException();",
    ], failures)

    require("MapObject frame engine", text["map"], [
        "public int FrameIndex",
        "FrameIndexChanged();",
        "public MirAction CurrentAction;",
        "public MirAnimation CurrentAnimation;",
        "public Frame CurrentFrame;",
        "public DateTime FrameStart;",
        "public Dictionary<MirAnimation, Frame> Frames;",
        "UpdateFrame();",
    ], failures)

    require("Client action dispatch", text["user"], [
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

    # The server receives native packets and delegates to PlayerObject. Movement is
    # Move, not Walk; the previous audit incorrectly expected a Walk method.
    require("Server PlayerObject", text["serverPlayer"], [
        "public partial class PlayerObject : MapObject",
        "public override ObjectType Race => ObjectType.Player",
        "public void Attack(",
        "public void Magic(",
    ], failures)
    require("Server action dispatch", text["connection"], [
        "public void Process(C.Move p)",
        "Player.Move(p.Direction, p.Distance);",
        "public void Process(C.Mount p)",
        "Player.Mount();",
        "public void Process(C.Attack p)",
        "Player.Attack(p.Direction, p.AttackMagic);",
        "public void Process(C.RangeAttack p)",
        "Player.RangeAttack(p.Direction, p.Target);",
        "public void Process(C.Magic p)",
        "Player.Magic(p);",
        "public void Process(C.FishingCast p)",
        "public void Process(C.Taming p)",
    ], failures)

    rows = [
        ("Standing", "Standing", "DIRECT", "Standing; native Stance/Creep/Horse/DragonRepulse/Channelling state overrides"),
        ("Walking", "Moving", "DIRECT_VARIANT", "Walking; HorseWalking/Creep variants"),
        ("Running", "Moving", "DIRECT_VARIANT", "Running for distance >= 2; HorseRunning when mounted"),
        ("Pushed", "Pushed", "DIRECT", "Pushed"),
        ("Attack", "Attack", "DIRECT", "Functions.GetAttackAnimation(class, weapon, magic)"),
        ("RangeAttack", "RangeAttack", "DIRECT", "Combat1"),
        ("Spell", "Spell", "DIRECT", "Functions.GetMagicAnimation(MagicType)"),
        ("Harvest", "Harvest", "DIRECT", "Harvest"),
        ("Struck", "Struck", "DIRECT", "Struck / HorseStruck"),
        ("Die", "Die", "DIRECT", "Die"),
        ("Dead", "Dead", "DIRECT", "Dead"),
        ("Show", "Show", "NO_DIRECT_PLAYER_ANIMATION", None),
        ("Hide", "Hide", "NO_DIRECT_PLAYER_ANIMATION", None),
        ("Mount", "Mount", "STATE_DRIVEN", "Horse state drives HorseStanding/Walking/Running/Struck; server uses Player.Mount()"),
        ("Fishing", "Fishing", "DIRECT", "FishingCast/FishingWait/FishingReel"),
        ("Taming", "Taming", "DIRECT", "TamingCast/TamingWait"),
        ("Idle", "Idle", "NO_DIRECT_PLAYER_ANIMATION", "DoNextAction falls back to Standing when no queued action"),
    ]

    native_unmapped = sorted(set(EXPECTED_ACTIONS) - direct_cases)
    result = {
        "schemaVersion": 2,
        "status": "PASS" if not failures else "FAIL",
        "zirconCommit": ZIRCON_COMMIT,
        "mirActionEnum": enum_actions,
        "directPlayerAnimationActions": sorted(direct_cases),
        "nativeActionsWithoutDirectPlayerAnimation": native_unmapped,
        "requestedAudit": [
            {"requested": r, "mirAction": m, "status": s, "animation": anim}
            for r, m, s, anim in rows
        ],
        "equipmentLayers": ["Body", "Hair", "Helmet", "Weapon1", "Weapon2", "Shield", "Horse"],
        "frameAuthority": {
            "frameSet": "FrameSet.Players",
            "frameIndexChanged": True,
            "directionalLayering": True,
            "spellEffectsBoundToFrames": True,
        },
        "serverAuthority": {
            "movement": "SConnection C.Move -> Player.Move",
            "mount": "SConnection C.Mount -> Player.Mount",
            "attack": "SConnection C.Attack -> Player.Attack",
            "rangeAttack": "SConnection C.RangeAttack -> Player.RangeAttack",
            "magic": "SConnection C.Magic -> Player.Magic",
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
        "- Server movement authority: `C.Move -> Player.Move`; there is no required `PlayerObject.Walk()` contract.",
        "",
        "| Requested behaviour | Native MirAction | Status | Native animation/behaviour |",
        "|---|---|---|---|",
    ]
    for requested, mir_action, status, animation in rows:
        lines.append(
            f"| {requested} | {mir_action} | {status} | {animation or 'none in PlayerObject.SetAnimation'} |"
        )
    lines += [
        "",
        "## Player visual stack",
        "",
        "Verified native Body, Hair, Helmet, Weapon1/Weapon2, Shield and Horse libraries/frames, including all eight direction branches and weapon/shield layering.",
        "",
        "## Frame-bound effects",
        "",
        "Verified native `FrameIndexChanged()` gates for SeismicSlam, CrushingWave, OffensiveBlow, Taming and Fishing, plus user movement/horse timing. Effect/projectile timing remains Zircon-owned.",
        "",
        "## Native enum actions without direct PlayerObject animation",
        "",
        ", ".join(native_unmapped) if native_unmapped else "None",
        "",
        "`Mount` is state-driven through `Horse`; `Show`, `Hide` and `Idle` are not assigned a direct animation by pinned `PlayerObject.SetAnimation()`. ORIGINS-DxR does not fabricate replacements.",
    ]
    if failures:
        lines += ["", "## Failures", ""] + [f"- {failure}" for failure in failures]
    lines.append("")
    a.md_output.parent.mkdir(parents=True, exist_ok=True)
    a.md_output.write_text("\n".join(lines), encoding="utf-8")

    print(
        f"ORIGINS-DxR player runtime audit: {result['status']}; "
        f"direct={len(direct_cases)}/{len(EXPECTED_ACTIONS)} MirAction values"
    )
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
