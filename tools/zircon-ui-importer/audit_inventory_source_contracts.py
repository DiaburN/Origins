#!/usr/bin/env python3
"""Strict source contract for InventoryDialog neutral/runtime boundaries."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"Inventory source contract changed: {label}: missing {needle!r}")

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--zircon-root',type=Path,required=True);args=parser.parse_args()
    spec=json.loads(args.spec.read_text(encoding='utf-8'))
    source=(args.zircon_root/'Client/Scenes/Views/InventoryDialog.cs').read_text(encoding='utf-8-sig')
    for needle,label in (
        ('GridSize = new Size(6, 8),','Inventory 6x8 grid'),
        ('GridType = GridType.Inventory,','Inventory grid type'),
        ('Index = 364,','Sort source artwork'),
        ('Index = 358,','Trash source artwork'),
        ('Index = 354,','Sell source artwork'),
        ('Visible = false','Sell initially hidden'),
        ('C.ItemSort packet = new C.ItemSort { Grid = GridType.Inventory };','Sort inventory packet'),
        ('if ((cell.Item.Flags & UserItemFlags.Locked) == UserItemFlags.Locked) return;','Trash locked-item guard'),
        ('if ((cell.Item.Flags & UserItemFlags.Marriage) == UserItemFlags.Marriage) return;','Trash marriage-item guard'),
        ('if (cell.GridType != GridType.Inventory) return;','Trash inventory-grid guard'),
        ('C.ItemDelete packet = new C.ItemDelete { Grid = cell.GridType, Slot = cell.Slot };','Trash delete packet'),
        ('GameScene.Game.CurrencyBox.Visible = !GameScene.Game.CurrencyBox.Visible;','Wallet currency toggle'),
        ('case InventoryMode.Normal:','Normal inventory mode'),
        ('TrashButton.Visible = true;','Normal mode Trash visible'),
        ('case InventoryMode.Sell:','Sell inventory mode'),
        ('SellButton.Visible = true;','Sell mode Sell visible'),
        ('CEnvir.Enqueue(new C.NPCSell { Links = links });','Sell server packet'),
    ): require(source,needle,label)
    window=next((w for w in spec.get('windows',[]) if w.get('field')=='InventoryBox'),None)
    if not window: raise SystemExit('InventoryBox missing from source manifest')
    names={c.get('name') for c in window.get('controls',[])}
    required={'Grid','SortButton','TrashButton','SellButton','WalletLabel','PrimaryCurrencyLabel','SecondaryCurrencyLabel','WeightLabel'}
    missing=sorted(required-names)
    if missing: raise SystemExit(f'Inventory source controls missing: {missing}')
    window['inventorySourceAudit']={'passed':True,'neutralMode':'Normal','grid':[6,8],'runtimeItemsInvented':False,'runtimeCurrenciesInvented':False,'runtimeWeightInvented':False,'serverActionsExecutedByReference':False}
    args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Inventory source contract: PASS (6x8, Normal mode, runtime items/currency neutral)')

if __name__=='__main__': main()
