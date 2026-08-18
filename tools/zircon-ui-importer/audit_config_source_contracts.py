#!/usr/bin/env python3
"""Strict source contract for DXConfigWindow as used by GameScene."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"Config source contract changed: {label}: missing {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    root = args.zircon_root
    config_src = (root / "Client/Envir/Config.cs").read_text(encoding="utf-8-sig")
    window_src = (root / "Client/Controls/DXConfigWindow.cs").read_text(encoding="utf-8-sig")
    game_src = (root / "Client/Scenes/GameScene.cs").read_text(encoding="utf-8-sig")
    globals_src = (root / "LibraryCore/Globals.cs").read_text(encoding="utf-8-sig")

    for control in ("FullScreenCheckBox", "BorderlessCheckbox", "GameSizeComboBox", "DefaultMonitorComboBox", "RenderingPipelineComboBox"):
        require(window_src, f"{control}.Enabled = ActiveScene is GameScene;", f"GameScene dynamic Enabled for {control}")

    for needle, label in (
        ("KeyBindButton.MouseClick += (o, e) => KeyBindWindow.Visible = !KeyBindWindow.Visible;", "KeyBind window toggle"),
        ("FullScreenCheckBox.Checked = Config.FullScreen;", "Fullscreen OnVisible binding"),
        ("BorderlessCheckbox.Checked = Config.Borderless;", "Borderless OnVisible binding"),
        ("VSyncCheckBox.Checked = Config.VSync;", "VSync OnVisible binding"),
        ("LanguageComboBox.ListBox.SelectItem(Config.Language);", "Language OnVisible selection"),
        ("SoundMusicBar.Value = Config.MusicVolume;", "Music volume OnVisible binding"),
        ("SoundSystemBar.Value = Config.SystemVolume;", "System volume OnVisible binding"),
        ("SoundPlayerBar.Value = Config.PlayerVolume;", "Player volume OnVisible binding"),
        ("SoundMonsterBar.Value = Config.MonsterVolume;", "Monster volume OnVisible binding"),
        ("SoundMagicBar.Value = Config.MagicVolume;", "Magic volume OnVisible binding"),
        ("Config.VSync = VSyncCheckBox.Checked;", "VSync local config update"),
        ("RenderingPipelineManager.ResetDevice();", "renderer reset side effect"),
        ("CEnvir.LoadLanguage();", "language reload side effect"),
        ("new C.SelectLanguage", "connected language packet"),
        ("new C.HelmetToggle", "helmet server toggle"),
        ("new C.ObservableSwitch", "observable server toggle"),
        ("ResetColoursButton.MouseClick +=", "colour reset action"),
    ):
        require(window_src, needle, label)

    require(game_src, "NetworkTab = { Enabled = false, TabButton = { Visible = false } },", "GameScene hides Network tab")
    require(game_src, "UITab = { TabButton = { Visible = true } },", "GameScene exposes UI tab")
    require(globals_src, '"English",', "English language source option")
    require(globals_src, '"Chinese",', "Chinese language source option")

    window = next((w for w in spec.get("windows", []) if w.get("field") == "ConfigBox"), None)
    if not window:
        raise SystemExit("ConfigBox missing from final manifest")
    source_pass = window.get("sourceConfigPass") or {}
    if source_pass.get("bindingCount", 0) < 25:
        raise SystemExit(f"Config source bindings unexpectedly low: {source_pass}")
    if source_pass.get("gameSceneDynamicEnabledControls") != [
        "FullScreenCheckBox", "BorderlessCheckbox", "GameSizeComboBox", "DefaultMonitorComboBox", "RenderingPipelineComboBox"
    ]:
        raise SystemExit(f"Config dynamic Enabled manifest drifted: {source_pass}")
    if source_pass.get("checkedInDefaultsOnly") is not True or source_pass.get("zirconIniInvented") is not False:
        raise SystemExit(f"Config reference provenance contract broken: {source_pass}")

    defaults = window.get("sourceConfigDefaults") or {}
    expected = {
        "FullScreen": True,
        "VSync": False,
        "Borderless": False,
        "GameSize": [1024, 768],
        "Language": "English",
        "SoundInBackground": True,
        "MusicVolume": 25,
        "SystemVolume": 25,
        "PlayerVolume": 25,
        "MonsterVolume": 25,
        "MagicVolume": 25,
        "DrawEffects": True,
        "DrawParticles": False,
        "DrawWeather": True,
        "ShowItemNames": True,
        "ShowMonsterNames": True,
        "ShowPlayerNames": True,
        "ShowUserHealth": True,
        "ShowMonsterHealth": True,
        "ShowDamageNumbers": True,
        "ShiftOpenChat": True,
        "RightClickDeTarget": True,
        "HideChatBar": True,
        "LogChat": True,
    }
    drift = {key: defaults.get(key) for key, value in expected.items() if defaults.get(key) != value}
    if drift:
        raise SystemExit(f"Config final manifest defaults drifted: {drift}")

    controls = {c.get("name"): c for c in window.get("controls", [])}
    language = controls.get("LanguageComboBox") or {}
    if [option.get("label") for option in language.get("comboOptions", [])] != ["English", "Chinese"]:
        raise SystemExit(f"Config LanguageComboBox source options drifted: {language.get('comboOptions')}")
    if language.get("comboSelectedOptionIndex") != 0:
        raise SystemExit(f"Config LanguageComboBox checked-in default is not English/index0: {language}")

    window["configSourceAudit"] = {
        "passed": True,
        "dynamicEnabledControlCount": 5,
        "languageOptions": ["English", "Chinese"],
        "networkTabHiddenInGameScene": True,
        "keyBindSourceWindow": "DXKeyBindWindow",
        "rendererOrServerSideEffectsExecutedByReference": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Config source contract: PASS ({source_pass.get('bindingCount')} bindings, English/Chinese, 5 GameScene Enabled overrides)")


if __name__ == "__main__":
    main()
