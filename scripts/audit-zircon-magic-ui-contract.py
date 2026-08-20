#!/usr/bin/env python3
"""Audit ORIGINS-DxR MagicDialog/MagicBar against pinned Zircon authority.

This gate deliberately does not implement spell behaviour. It proves that:
- the native pinned Zircon client owns filtering, user-magic state, key assignment,
  duplicate-key eviction, SpellSet selection, icon updates and cooldowns;
- the ORIGINS browser reference consumes canonical MagicInfo/player state only for
  presentation and does not mutate key bindings or enqueue gameplay packets;
- the closed MagicBar reference preserves Zircon's 24-slot / 4-set geometry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ZIRCON_COMMIT = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"


def read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8-sig", errors="strict")


def require_tokens(name: str, text: str, tokens: list[str], failures: list[str]) -> None:
    for token in tokens:
        if token not in text:
            failures.append(f"{name}: missing source contract token: {token}")


def reject_tokens(name: str, text: str, tokens: list[str], failures: list[str]) -> None:
    for token in tokens:
        if token in text:
            failures.append(f"{name}: forbidden runtime-authority token present: {token}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--zircon", type=Path, default=Path("vendor/zircon"))
    parser.add_argument("--json-output", type=Path, default=Path("artifacts/magic-ui/magic-ui-contract.json"))
    parser.add_argument("--md-output", type=Path, default=Path("docs/generated/ORIGINS_DXR_MAGIC_UI_STATUS.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    zircon = (repo / args.zircon).resolve() if not args.zircon.is_absolute() else args.zircon

    paths = {
        "magicDialog": zircon / "Client/Scenes/Views/MagicDialog.cs",
        "magicBar": zircon / "Client/Scenes/Views/MagicBarDialog.cs",
        "browserRuntime": repo / "apps/zircon-ui-reference/zircon-magic-runtime.js",
        "browserIndex": repo / "apps/zircon-ui-reference/index.html",
        "barAugment": repo / "tools/zircon-ui-importer/augment_magic_bar_reference.py",
        "magicInfo": repo / "database/generated/zircon-system/LibraryCore__Library_SystemModels_MagicInfo.json",
    }

    failures: list[str] = []
    texts: dict[str, str] = {}
    for name, path in paths.items():
        try:
            texts[name] = read(path)
        except Exception as exc:
            failures.append(f"{name}: cannot read {path}: {exc}")
            texts[name] = ""

    dialog = texts["magicDialog"]
    bar = texts["magicBar"]
    browser = texts["browserRuntime"]
    index = texts["browserIndex"]
    augment = texts["barAugment"]

    native_dialog_tokens = [
        "Globals.MagicInfoList.Binding.ToList()",
        "x1.NeedLevel1.CompareTo(x2.NeedLevel1)",
        "case MirClass.Warrior:",
        "case MirClass.Wizard:",
        "case MirClass.Taoist:",
        "case MirClass.Assassin:",
        "magic.Class != MapObject.User.Class",
        "magic.School == MagicSchool.None",
        "magic.School == MagicSchool.Discipline",
        "userMagic.ItemRequired",
        "ItemEffect.MagicRing",
        "x.Info.Shape == magic.Index",
        "SchoolTabs.TryGetValue(magic.School",
        "new MagicTab(magic.School)",
        "tab.ScrollBar.DoMouseWheel",
        "Image.Index = Info.Icon",
        "NameLabel.Text = Info.Name",
        "NeedLevel1",
        "Experience1",
        "Experience2",
        "Experience3",
        "Not\\r\\nLearned",
        "GameScene.Game.MagicBarBox.SpellSet",
        "magic.Set1Key = key",
        "magic.Set2Key = key",
        "magic.Set3Key = key",
        "magic.Set4Key = key",
        "pair.Value.Set1Key == magic.Set1Key",
        "pair.Value.Set2Key == magic.Set2Key",
        "pair.Value.Set3Key == magic.Set3Key",
        "pair.Value.Set4Key == magic.Set4Key",
        "pair.Value.Set1Key = SpellKey.None",
        "pair.Value.Set2Key = SpellKey.None",
        "pair.Value.Set3Key = SpellKey.None",
        "pair.Value.Set4Key = SpellKey.None",
        "CEnvir.Enqueue(new C.MagicKey",
        "GameScene.Game.MagicBarBox.UpdateIcons()",
    ]
    require_tokens("pinned MagicDialog", dialog, native_dialog_tokens, failures)

    native_bar_tokens = [
        "_SpellSet = 1;",
        "SpellSet = Math.Max(1, SpellSet - 1)",
        "SpellSet = Math.Min(4, SpellSet + 1)",
        "for (int i = 0; i < 24; i++)",
        "$\"Spell{(i + 1):00}\"",
        "const int IconsPerRow = 12;",
        "bool isVisible = i < 12;",
        "case 1:",
        "return x.Set1Key == pair.Key;",
        "return x.Set2Key == pair.Key;",
        "return x.Set3Key == pair.Key;",
        "return x.Set4Key == pair.Key;",
        "pair.Value.Index = magic.Info.Icon",
        "UpdateBorder(magic.Info.School)",
        "SpellKey.Spell13",
        "SpellKey.Spell24",
        "magic.NextCast",
        "GameScene.Game.ToggleTime",
        "Cooldowns[pair.Key].Text",
    ]
    require_tokens("pinned MagicBar", bar, native_bar_tokens, failures)

    browser_tokens = [
        "../../database/generated/zircon-system/LibraryCore__Library_SystemModels_MagicInfo.json",
        "Warrior: 0",
        "Wizard: 1",
        "Taoist: 2",
        "Assassin: 3",
        "function playerRows(rows)",
        "Number(info.Class) !== state.class",
        "Number(info.School) === 0",
        "Number(info.School) === 20",
        "ItemRequired",
        "RequiredItemEquipped",
        "Number(info.NeedLevel1)",
        "Number(info.Icon)",
        "info.Name",
        "Experience1",
        "Experience2",
        "Experience3",
        "function currentKey(user)",
        "setPlayerState(next = {})",
    ]
    require_tokens("ORIGINS MagicDialog presentation runtime", browser, browser_tokens, failures)

    # The browser reference must not become a second spell authority. It can display
    # authoritative state, but it must never write spell keys or enqueue gameplay.
    browser_forbidden = [
        "C.MagicKey",
        "CEnvir.Enqueue",
        "Enqueue(new",
        "Set1Key =",
        "Set2Key =",
        "Set3Key =",
        "Set4Key =",
        "NextCast =",
        "ToggleTime =",
    ]
    reject_tokens("ORIGINS MagicDialog presentation runtime", browser, browser_forbidden, failures)

    require_tokens(
        "ORIGINS reference shell",
        index,
        ['<script type="module" src="zircon-magic-runtime.js"></script>'],
        failures,
    )
    require_tokens(
        "MagicBar closed-reference geometry",
        augment,
        [
            "for i in range(24):",
            '"slots": 24',
            '"initialVisibleSlots": 12',
            '"spellSetInitial": 1',
            '"spellSetRange": [1, 4]',
            '"runtimeMagicDataInvented": False',
            '"RuntimeIndex": "magic.Info.Icon or -1"',
        ],
        failures,
    )

    magic_rows = []
    try:
        magic_rows = json.loads(texts["magicInfo"])
        if not isinstance(magic_rows, list):
            failures.append("canonical MagicInfo: expected JSON array")
            magic_rows = []
    except Exception as exc:
        failures.append(f"canonical MagicInfo: parse failed: {exc}")

    class_counts = {"Warrior": 0, "Wizard": 0, "Taoist": 0, "Assassin": 0}
    class_ids = {"Warrior": 0, "Wizard": 1, "Taoist": 2, "Assassin": 3}
    for name, class_id in class_ids.items():
        class_counts[name] = sum(1 for row in magic_rows if int(row.get("Class", -999)) == class_id)
        if class_counts[name] == 0:
            failures.append(f"canonical MagicInfo: no rows for {name}")

    result = {
        "schemaVersion": 1,
        "zirconCommit": ZIRCON_COMMIT,
        "status": "PASS" if not failures else "FAIL",
        "policy": {
            "browserIsPresentationOnly": True,
            "nativeZirconOwnsKeyMutation": True,
            "nativeZirconOwnsCooldowns": True,
            "nativeZirconOwnsSpellSet": True,
            "javascriptGameplayPacketsAllowed": False,
        },
        "canonicalMagicInfoRows": len(magic_rows),
        "canonicalMagicInfoRowsByClass": class_counts,
        "contracts": {
            "MagicDialog": {
                "classFiltering": True,
                "dynamicSchoolTabs": True,
                "scroll": True,
                "itemRequired": True,
                "learnedState": True,
                "requiredLevel": True,
                "magicLevelExperience": True,
                "iconNameKey": True,
            },
            "MagicBar": {
                "spellSets": 4,
                "slots": 24,
                "duplicateKeysEvictedByNativeClient": True,
                "iconsFromMagicInfo": True,
                "secondRowFromSpell13": True,
                "cooldownFromNativeNextCast": True,
            },
        },
        "failures": failures,
    }

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# ORIGINS-DxR — Magic UI authority contract",
        "",
        f"- Gate: **{result['status']}**",
        f"- Zircon authority: `{ZIRCON_COMMIT}`",
        f"- Canonical MagicInfo rows visible to presentation: **{len(magic_rows)}**",
        "- Browser role: **presentation only**; no spell-key mutation, no gameplay packet enqueue.",
        "- Native Zircon role: class/school filtering, ItemRequired, learned state, experience, SpellSet 1–4, Spell01–24, duplicate-key eviction, icon update and cooldown authority.",
        "",
        "| Class | MagicInfo rows |",
        "|---|---:|",
    ]
    lines.extend(f"| {name} | {count} |" for name, count in class_counts.items())
    lines.extend([
        "",
        "## Verified native contracts",
        "",
        "- `MagicDialog.CreateTabs()` uses Zircon `Globals.MagicInfoList` and the current `MapObject.User` class/magics.",
        "- `MagicCell` reads `MagicInfo.Icon/Name/NeedLevel/Experience` and native `ClientUserMagic` state.",
        "- `MagicCell.Image_KeyDown` owns key assignment and removes duplicate keys across Set1/Set2/Set3/Set4 before sending `C.MagicKey`.",
        "- `MagicBarDialog` owns 24 SpellKey slots, four spell sets, second-row visibility, school borders and cooldown display.",
        "",
        "## ORIGINS browser reference rule",
        "",
        "`apps/zircon-ui-reference/zircon-magic-runtime.js` may render canonical MagicInfo/player state for visual QA, but it is explicitly rejected by this gate if it starts writing Set1Key..Set4Key, NextCast/ToggleTime, or gameplay packets.",
    ])
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text("\n".join(lines), encoding="utf-8")

    print(f"ORIGINS-DxR Magic UI authority contract: {result['status']}; MagicInfo={len(magic_rows)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
