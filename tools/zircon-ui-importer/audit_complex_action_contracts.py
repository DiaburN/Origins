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

    storage = read(args.zircon_root, "Client/Scenes/Views/StorageDialog.cs")
    for needle, label in (
        ("if (IsVisible)\n                GameScene.Game.InventoryBox.Visible = true;", "Storage opens Inventory"),
        ("ItemTypeComboBox.ListBox.SelectItem(null);", "Storage initial/clear All filter"),
        ("ItemNameTextBox.TextBox.Text = string.Empty;", "Storage clear name filter"),
        ('new DXMessageBox("Are you sure you want to sort your storage?", "Confirm Sort", DXMessageBoxButtons.YesNo)', "Storage sort confirmation"),
        ("Grid = StorageTab.Visible ? GridType.Storage : GridType.PartsStorage", "Storage sort grid selection"),
        ("CEnvir.Enqueue(packet);", "Storage sort packet enqueue"),
        ("Visible = false,\n                BackColour = Color.Empty", "Storage PartsTab starts hidden"),
    ): require(storage, needle, label)

    group = read(args.zircon_root, "Client/Scenes/Views/GroupDialog.cs")
    globals_source = read(args.zircon_root, "LibraryCore/Globals.cs")
    for needle, label in (
        ("GroupLFGInputWindow window = new GroupLFGInputWindow()", "Group opens LFG input window"),
        ("EnableButton = { Enabled = false },", "Group LFG caller disables Enable initially"),
        ("Modal = true", "Group LFG caller modal"),
        ("public int CountValue = 4;", "Group LFG initial count"),
        ('public string TypeValue = "PvE";', "Group LFG initial type"),
        ("length >= 2 && length <= 16", "Group LFG name validation"),
        ("MinValue = 2,", "Group LFG minimum count"),
        ("MaxValue = Globals.GroupLimit,", "Group LFG maximum count"),
        ("new C.GroupLFGUpdate", "Group LFG network update"),
    ): require(group, needle, label)
    require(globals_source, "GroupLimit = 15,", "GroupLimit constant")
    require(globals_source, "LookingForGroupMinutes = 60,", "LFG duration constant")

    combo = read(args.zircon_root, "Client/Controls/DXComboBox.cs")
    require(combo, "public const int DefaultNormalHeight = 16;", "DXComboBox default normal height")
    require(combo, "DropDownHeight = 123;", "DXComboBox dropdown height")
    require(combo, "Index = 795,", "DXComboBox down-arrow artwork")
    require(combo, "Parent = ActiveScene,", "DXComboBox listbox ActiveScene parent")
    require(combo, "Showing = !Showing;", "DXComboBox arrow toggle")
    require(combo, "SelectedLabel.Text = ListBox.SelectedItem?.Label.Text ?? string.Empty;", "DXComboBox selected label")
    require(combo, "Showing = false;", "DXComboBox closes after selection")

    spec["complexActionAudit"] = {
        "contractCount": 8,
        "contracts": {
            "TradeDialog": "confirm disables then C.TradeConfirm; gold modal requires runtime user gold; close packet only while trading",
            "ExitDialog": "modal; 10-second combat gate; logout/application-close actions remain runtime gated",
            "ConsignmentDialog": "Search/Consign tab artwork and dependent visibility set by SetActiveTab",
            "GameStoreDialog": "Alphabetical default sort; Hunt/Game Gold toggle rebuilds local store state",
            "CommunicationDialog": "Friend/Received/Send/Block backgrounds and button visibility; Send resets draft; ReadMail runtime-only",
            "StorageDialog": "opening forces Inventory visible; filters clear to All/empty; sorting is confirmed then server-enqueued",
            "GroupLFGInputWindow": "modal no-existing-LFG state: PvE, Count=4, 2..15, valid name 2..16, 60-minute source duration",
            "DXComboBox": "16px normal, 123px dropdown, GameInter 795 arrow, ActiveScene listbox, selection closes",
        },
        "runtimeServerDataInvented": False,
        "source": "current Suprcode/Zircon C# source",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Complex source action contracts: 8/8 PASS")


if __name__ == "__main__": main()
