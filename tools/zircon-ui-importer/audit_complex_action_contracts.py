#!/usr/bin/env python3
"""Lock high-value non-trivial Zircon UI behaviors to current source.

These contracts cover state changes that are more complex than direct window
visibility. Runtime/server payloads are documented but never fabricated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"Complex action contract changed: {label}: missing {needle!r}")


def read(root: Path, relative: str) -> str:
    path = root / relative
    if not path.exists(): raise SystemExit(f"Missing Zircon source for complex-action audit: {relative}")
    return path.read_text(encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))

    trade = read(args.zircon_root, "Client/Scenes/Views/TradeDialog.cs")
    require(trade, "ConfirmButton.Enabled = false;", "Trade confirm disables immediately")
    require(trade, "new C.TradeConfirm()", "Trade confirm packet")
    require(trade, 'new DXItemAmountWindow("Trade Gold"', "Trade gold amount modal")
    require(trade, "if (!IsTrading || GameScene.Game.Observer) return;", "Trade close runtime guard")
    require(trade, "new C.TradeClose()", "Trade close packet")

    exit_dialog = read(args.zircon_root, "Client/Scenes/Views/ExitDialog.cs")
    require(exit_dialog, "Modal = true;", "Exit dialog modal")
    if exit_dialog.count("MapObject.User.CombatTime.AddSeconds(10)") < 2:
        raise SystemExit("Complex action contract changed: Exit combat 10-second gate")
    require(exit_dialog, "new C.Logout()", "Exit to-select logout packet")
    require(exit_dialog, "Exiting = true;", "Exit application state")
    require(exit_dialog, "CEnvir.Target.Close();", "Exit application close")

    consign = read(args.zircon_root, "Client/Scenes/Views/ConsignmentDialog.cs")
    require(consign, "TabImage.Index = search ? 301 : 302;", "Consignment tab artwork")
    for needle, label in (
        ("BuyButton.Visible = search;", "Consignment buy visibility"),
        ("ConsignButton.Visible = !search;", "Consignment consign visibility"),
        ("RemoveListingButton.Visible = !search;", "Consignment remove visibility"),
        ("BuyGuildBox.Visible = search;", "Consignment buy-guild visibility"),
        ("ConsignGuildBox.Visible = !search;", "Consignment consign-guild visibility"),
        ("ResultCountLabel.Visible = search;", "Consignment search count visibility"),
        ("ConsignResultCountLabel.Visible = !search;", "Consignment consign count visibility"),
        ("SearchTab.TabButton.InvokeMouseClick();", "Consignment initial Search tab"),
    ): require(consign, needle, label)

    store = read(args.zircon_root, "Client/Scenes/Views/GameStoreDialog.cs")
    require(store, "SortBox.ListBox.SelectItem(MarketPlaceStoreSort.Alphabetical);", "GameStore initial sort")
    require(store, "UseHuntGold = !UseHuntGold;", "GameStore currency toggle")
    require(store, "ItemList.UseHuntGold = UseHuntGold;", "GameStore item-list currency propagation")
    require(store, "RefreshCurrency();", "GameStore currency refresh")
    require(store, "BuildFolderTree();", "GameStore currency folder rebuild")
    require(store, "RefreshItems();", "GameStore item refresh")

    communication = read(args.zircon_root, "Client/Scenes/Views/CommunicationDialog.cs")
    for index in (201, 202, 203, 204):
        require(communication, f"BackgroundImage.Index = {index};", f"Communication tab background {index}")
    for needle, label in (
        ("FriendAddButton.Visible = true;", "Communication friends controls"),
        ("ReceivedCollectAllButton.Visible = true;", "Communication received controls"),
        ("SendButton.Visible = true;", "Communication send controls"),
        ("BlockAddButton.Visible = true;", "Communication block controls"),
        ("ReadMail = null;", "Communication tab read-state reset"),
        ("SendRecipientBox.TextBox.Text = string.Empty;", "Communication Send clears recipient"),
        ("SendMessageBox.TextBox.Text = string.Empty;", "Communication Send clears message"),
        ("SendSubjectBox.TextBox.Text = string.Empty;", "Communication Send clears subject"),
        ("SendGoldBox.Value = 0;", "Communication Send clears gold"),
        ("ReadTab.Visible = ReadMail != null;", "Communication read-mail runtime visibility"),
    ): require(communication, needle, label)

    combo = read(args.zircon_root, "Client/Controls/DXComboBox.cs")
    require(combo, "public const int DefaultNormalHeight = 16;", "DXComboBox default normal height")
    require(combo, "DropDownHeight = 123;", "DXComboBox dropdown height")
    require(combo, "Index = 795,", "DXComboBox down-arrow artwork")
    require(combo, "Parent = ActiveScene,", "DXComboBox listbox ActiveScene parent")
    require(combo, "Showing = !Showing;", "DXComboBox arrow toggle")
    require(combo, "SelectedLabel.Text = ListBox.SelectedItem?.Label.Text ?? string.Empty;", "DXComboBox selected label")
    require(combo, "Showing = false;", "DXComboBox closes after selection")

    spec["complexActionAudit"] = {
        "contractCount": 6,
        "contracts": {
            "TradeDialog": "confirm disables then C.TradeConfirm; gold modal requires runtime user gold; close packet only while trading",
            "ExitDialog": "modal; 10-second combat gate; logout/application-close actions remain runtime gated",
            "ConsignmentDialog": "Search/Consign tab artwork and dependent visibility set by SetActiveTab",
            "GameStoreDialog": "Alphabetical default sort; Hunt/Game Gold toggle rebuilds local store state",
            "CommunicationDialog": "Friend/Received/Send/Block backgrounds and button visibility; Send resets draft; ReadMail runtime-only",
            "DXComboBox": "16px normal, 123px dropdown, GameInter 795 arrow, ActiveScene listbox, selection closes",
        },
        "runtimeServerDataInvented": False,
        "source": "current Suprcode/Zircon C# source",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Complex source action contracts: 6/6 PASS")


if __name__ == "__main__": main()
