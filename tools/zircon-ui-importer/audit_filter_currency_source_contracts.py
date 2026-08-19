#!/usr/bin/env python3
"""Strict current-source contracts for FilterDropDialog and CurrencyDialog.

FilterDrop owns ten deterministic constructor rows. Currency owns only the
CurrencyTree shell/scrollbar deterministically; headers/items remain runtime
user-currency data and must stay absent from the neutral reference.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def req(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"Filter/Currency source contract changed: {label}: missing {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    filter_src = (args.zircon_root / "Client/Scenes/Views/FilterDropDialog.cs").read_text(encoding="utf-8-sig")
    currency_src = (args.zircon_root / "Client/Scenes/Views/CurrencyDialog.cs").read_text(encoding="utf-8-sig")
    config_src = (args.zircon_root / "Client/Envir/Config.cs").read_text(encoding="utf-8-sig")

    for needle, label in (
        ("public Dictionary<int, DXTextBox> DropFiltersMap = new Dictionary<int, DXTextBox>();", "filter map"),
        ("SetClientSize(new Size(266, 371));", "filter client size"),
        ("for (int i = 0; i < 10; i++)", "ten-filter constructor loop"),
        ("DXLabel filterLabel = new DXLabel", "filter label creation"),
        ("Text = string.Format(CEnvir.Language.FilterDialogFilterLabel, (i + 1))", "filter label text"),
        ("filterLabel.Location = new Point(20, 50 + (10 + filterLabel.Size.Height) * i);", "filter label location"),
        ("DropFiltersMap[i] = new DXTextBox", "filter textbox creation"),
        ("BorderColour = Constants.PrimaryColour,", "filter border colour"),
        ("Location = new Point(90, filterLabel.Location.Y),", "filter textbox location"),
        ("Size = new Size(150, 18)", "filter textbox size"),
        ("List<string> dropItems = new List<string>();", "filter save list"),
        ("dropItems.Add(DropFiltersMap[i].TextBox.Text);", "filter save row read"),
        ("Config.HighlightedItems = String.Join(\",\", dropItems);", "filter save config"),
        ("GameScene.Game.ReceiveChat(CEnvir.Language.FilterConfigSaved, MessageType.System);", "filter save chat"),
    ):
        req(filter_src, needle, label)
    req(config_src, "public static string HighlightedItems { get; set; } = string.Empty;", "checked-in highlighted-items default")

    for needle, label in (
        ("SetClientSize(new Size(227, 7 * 43 + 1));", "currency client size"),
        ("BindTree = new CurrencyTree", "currency tree"),
        ("Location = new Point(ClientArea.X, ClientArea.Y)", "currency tree location"),
        ("Size = new Size(ClientArea.Width, ClientArea.Height)", "currency tree size"),
        ("private const int HeaderHeight = 22;", "currency header height"),
        ("private const int CurrencyHeight = 42;", "currency item height"),
        ("ScrollBar.Size = new Size(14, Size.Height);", "currency scrollbar size"),
        ("ScrollBar.Location = new Point(Size.Width - 14, 0);", "currency scrollbar location"),
        ("ScrollBar.VisibleSize = Size.Height;", "currency scrollbar visible size"),
        ("Change = 22,", "currency scrollbar change"),
        ("ScrollBar.MaxValue = TotalCount;", "currency scrollbar max"),
        ("foreach (ClientUserCurrency bind in GameScene.Game.User.Currencies.OrderBy(x => x.Info.Category))", "runtime currency population"),
        ("BindTree.ListChanged();", "runtime currency tree refresh"),
        ("foreach (KeyValuePair<string, List<ClientUserCurrency>> pair in TreeList)", "runtime category rows"),
        ("CurrencyTreeHeader header = new CurrencyTreeHeader", "runtime currency header creation"),
        ("CurrencyItem entry = new CurrencyItem", "runtime currency item creation"),
    ):
        req(currency_src, needle, label)

    by_field = {window.get("field"): window for window in spec.get("windows", [])}
    filter_window = by_field.get("FilterDropBox")
    currency_window = by_field.get("CurrencyBox")
    if not filter_window or not currency_window:
        raise SystemExit("FilterDropBox/CurrencyBox missing from manifest")

    generated = [
        control for control in filter_window.get("controls", [])
        if str(control.get("name") or "").startswith("FilterDropGenerated")
    ]
    labels = [control for control in generated if control.get("type") == "DXLabel"]
    textboxes = [control for control in generated if control.get("type") == "DXTextBox"]
    loop = filter_window.get("filterDropSourceLoop") or {}
    expected_loop = {
        "passed": True,
        "count": 10,
        "labels": 10,
        "textBoxes": 10,
        "controlsMaterialized": 20,
        "templateControlsRemoved": 2,
        "netControlsAdded": 18,
        "textBoxX": 90,
        "textBoxSize": [150, 18],
        "border": True,
        "borderColour": "Constants.PrimaryColour",
        "checkedInConfigHighlightedItems": "",
        "runtimeHighlightedItemsInvented": False,
    }
    for key, value in expected_loop.items():
        if loop.get(key) != value:
            raise SystemExit(f"FilterDrop source loop contract drifted: {key}={loop.get(key)!r}, expected {value!r}")
    if len(generated) != 20 or len(labels) != 10 or len(textboxes) != 10:
        raise SystemExit(f"FilterDrop generated controls drifted: total={len(generated)} labels={len(labels)} textboxes={len(textboxes)}")
    if any((control.get("properties") or {}).get("Size") != "new Size(150, 18)" for control in textboxes):
        raise SystemExit("FilterDrop textbox current source size drifted")
    if any((control.get("properties") or {}).get("Border") != "true" or (control.get("properties") or {}).get("BorderColour") != "Constants.PrimaryColour" for control in textboxes):
        raise SystemExit("FilterDrop textbox current source border drifted")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("FilterDrop generated rows invented runtime payloads")

    tree = currency_window.get("deterministicCurrencyTree") or {}
    expected_tree = {
        "passed": True,
        "controlsAdded": 2,
        "treeShells": 1,
        "scrollbars": 1,
        "runtimeHeadersInvented": False,
        "runtimeCurrencyItemsInvented": False,
        "runtimeCurrencyDataInvented": False,
        "sourceClientSize": [227, 302],
    }
    for key, value in expected_tree.items():
        if tree.get(key) != value:
            raise SystemExit(f"Currency deterministic tree contract drifted: {key}={tree.get(key)!r}, expected {value!r}")
    if any(control.get("sourceType") in {"CurrencyTreeHeader", "CurrencyItem"} for control in currency_window.get("controls", [])):
        raise SystemExit("Currency runtime user rows were pre-created")

    filter_window["filterDropSourceAudit"] = {
        "passed": True,
        "filterCount": 10,
        "deterministicControls": 20,
        "netControlsAdded": 18,
        "checkedInHighlightedItems": "",
        "runtimeFilterConfigInvented": False,
    }
    currency_window["currencySourceAudit"] = {
        "passed": True,
        "deterministicControls": 2,
        "neutralHeaderCount": 0,
        "neutralCurrencyCount": 0,
        "runtimeCurrenciesInvented": False,
        "treeBorderAndScrollbarPreserved": True,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Filter/Currency source contract: PASS (FilterDrop 10+10; CurrencyTree shell 2; runtime payloads neutral)")


if __name__ == "__main__":
    main()
