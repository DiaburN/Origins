#!/usr/bin/env python3
"""Bind DXConfigWindow controls to deterministic checked-in Config.cs defaults.

DXConfigWindow.OnVisibleChanged copies Config.* into controls. The reference
viewer has no Zircon.ini/user machine state, so the only truthful standalone
state is Config.cs' checked-in defaults. Runtime monitor/pipeline/resolution lists
remain unresolved and are never invented.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_defaults(text: str) -> dict[str, object]:
    values: dict[str, object] = {}
    intro = re.search(r"IntroSceneSize\s*=\s*new Size\(\s*(\d+)\s*,\s*(\d+)\s*\)", text)
    intro_size = [int(intro.group(1)), int(intro.group(2))] if intro else None
    pattern = re.compile(r"public\s+static\s+(bool|int|string|Size)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{\s*get;\s*set;\s*\}\s*(?:=\s*([^;]+))?;")
    for match in pattern.finditer(text):
        type_name, name, expression = match.groups()
        expression = expression.strip() if expression else None
        if type_name == "bool": values[name] = expression == "true" if expression is not None else False
        elif type_name == "int":
            if expression and re.fullmatch(r"-?\d+", expression): values[name] = int(expression)
        elif type_name == "string":
            if expression == "string.Empty": values[name] = ""
            elif expression:
                literal = re.fullmatch(r'"((?:\\.|[^"\\])*)"', expression)
                if literal:
                    try: values[name] = json.loads('"' + literal.group(1) + '"')
                    except json.JSONDecodeError: values[name] = literal.group(1)
        elif type_name == "Size":
            literal = re.fullmatch(r"new Size\(\s*(\d+)\s*,\s*(\d+)\s*\)", expression or "")
            if literal: values[name] = [int(literal.group(1)), int(literal.group(2))]
            elif expression == "IntroSceneSize" and intro_size: values[name] = intro_size
    return values


def resolve_default_option(control: dict, default: object) -> int | None:
    options = control.get("comboOptions") or []
    if default is None or not options: return None
    if isinstance(default, list) and len(default) == 2:
        expected_label = f"{default[0]} x {default[1]}"
        for index, option in enumerate(options):
            if option.get("label") == expected_label: return index
        return None
    expected = str(default)
    for index, option in enumerate(options):
        value = str(option.get("valueExpression") or "").strip()
        quoted = re.fullmatch(r'"((?:\\.|[^"\\])*)"', value)
        if quoted:
            try: decoded = json.loads(value)
            except json.JSONDecodeError: decoded = quoted.group(1)
            if decoded == default: return index
        if option.get("label") == expected: return index
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    config_path = args.zircon_root / "Client" / "Envir" / "Config.cs"
    window_path = args.zircon_root / "Client" / "Controls" / "DXConfigWindow.cs"
    game_path = args.zircon_root / "Client" / "Scenes" / "GameScene.cs"
    for path in (config_path, window_path, game_path):
        if not path.exists(): raise SystemExit(f"Config source missing: {path}")
    config_text = config_path.read_text(encoding="utf-8-sig")
    window_text = window_path.read_text(encoding="utf-8-sig")
    game_text = game_path.read_text(encoding="utf-8-sig")
    defaults = parse_defaults(config_text)

    config_window = next((item for item in spec.get("windows", []) if item.get("field") == "ConfigBox"), None)
    if not config_window: raise SystemExit("ConfigBox missing from source manifest")
    by_name = {control.get("name"): control for control in config_window.get("controls", [])}

    bindings: list[dict] = []
    resolved_combo_defaults = 0
    patterns = (
        ("checked", re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.Checked\s*=\s*Config\.([A-Za-z_][A-Za-z0-9_]*)\s*;")),
        ("value", re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.Value\s*=\s*Config\.([A-Za-z_][A-Za-z0-9_]*)\s*;")),
        ("muted", re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.Muted\s*=\s*Config\.([A-Za-z_][A-Za-z0-9_]*)\s*;")),
        ("selected", re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.ListBox\.SelectItem\(Config\.([A-Za-z_][A-Za-z0-9_]*)\)\s*;")),
    )
    seen: set[tuple[str, str, str]] = set()
    for kind, pattern in patterns:
        for control_name, prop in pattern.findall(window_text):
            key = (control_name, prop, kind)
            if key in seen: continue
            seen.add(key)
            control = by_name.get(control_name)
            if not control: continue
            default = defaults.get(prop)
            entry = {"control": control_name, "configProperty": prop, "kind": kind, "default": default}
            bindings.append(entry)
            control.setdefault("sourceConfigBindings", []).append(entry)
            if kind == "selected":
                selected = resolve_default_option(control, default)
                if selected is not None:
                    control["comboSelectedOptionIndex"] = selected
                    control["comboSelectedSource"] = f"Config.{prop} checked-in default"
                    resolved_combo_defaults += 1

    enabled_in_game = ["FullScreenCheckBox", "BorderlessCheckbox", "GameSizeComboBox", "DefaultMonitorComboBox", "RenderingPipelineComboBox"]
    for name in enabled_in_game:
        control = by_name.get(name)
        if not control: raise SystemExit(f"Config source control missing for GameScene enable override: {name}")
        if f"{name}.Enabled = ActiveScene is GameScene;" not in window_text:
            raise SystemExit(f"Config GameScene dynamic Enabled source changed: {name}")
        control["sourceEnabledInGameScene"] = True

    if "NetworkTab = { Enabled = false, TabButton = { Visible = false } }" not in game_text.replace("\r", ""):
        if not ("NetworkTab = { Enabled = false" in game_text and "UITab = { TabButton = { Visible = true } }" in game_text):
            raise SystemExit("GameScene Config Network/UI tab override changed")
    config_window["gameSceneConfigOverrides"] = {"NetworkTabEnabled": False,"NetworkTabButtonVisible": False,"UITabButtonVisible": True,"activeScene": "GameScene"}

    required_defaults = {
        "FullScreen": True,"VSync": False,"LimitFPS": False,"GameSize": [1024, 768],"ClipMouse": False,"DebugLabel": False,"Language": "English","Borderless": False,"SmoothMove": False,
        "SoundInBackground": True,"SystemVolume": 25,"MusicVolume": 25,"PlayerVolume": 25,"MonsterVolume": 25,"MagicVolume": 25,
        "DrawEffects": True,"DrawParticles": False,"DrawWeather": True,"ShowTargetOutline": True,"ShowItemNames": True,"ShowMonsterNames": True,"ShowPlayerNames": True,"ShowUserHealth": True,"ShowMonsterHealth": True,"ShowDamageNumbers": True,
        "ShiftOpenChat": True,"RightClickDeTarget": True,"HideChatBar": True,"MonsterBoxVisible": True,"LogChat": True,
    }
    drift = {key: defaults.get(key) for key, value in required_defaults.items() if defaults.get(key) != value}
    if drift: raise SystemExit(f"Checked-in Config defaults changed; review reference state: {drift}")

    language = by_name.get("LanguageComboBox")
    if not language or [option.get("label") for option in language.get("comboOptions", [])] != ["English", "Chinese"]:
        raise SystemExit(f"Config LanguageComboBox source options missing before default binding: {language}")
    if language.get("comboSelectedOptionIndex") != 0:
        raise SystemExit(f"Config.Language=English did not resolve to LanguageComboBox index 0: {language}")

    config_window["sourceConfigDefaults"] = {key: defaults.get(key) for key in sorted({entry["configProperty"] for entry in bindings})}
    config_window["sourceConfigPass"] = {
        "bindingCount": len(bindings),"resolvedComboDefaults": resolved_combo_defaults,"gameSceneDynamicEnabledControls": enabled_in_game,"checkedInDefaultsOnly": True,"zirconIniInvented": False,"runtimeRenderingEnvironmentInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Config source defaults promoted: {len(bindings)} OnVisible bindings; combo defaults={resolved_combo_defaults}; GameScene dynamic enabled={len(enabled_in_game)}")


if __name__ == "__main__": main()
