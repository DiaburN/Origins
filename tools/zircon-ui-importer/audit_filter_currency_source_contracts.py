#!/usr/bin/env python3
"""Strict source contracts for FilterDropDialog and CurrencyDialog neutral state."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def req(text,needle,label):
    if needle not in text: raise SystemExit(f"Filter/Currency source contract changed: {label}: missing {needle!r}")

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    filter_src=(a.zircon_root/'Client/Scenes/Views/FilterDropDialog.cs').read_text(encoding='utf-8-sig')
    currency_src=(a.zircon_root/'Client/Scenes/Views/CurrencyDialog.cs').read_text(encoding='utf-8-sig')
    config_src=(a.zircon_root/'Client/Envir/Config.cs').read_text(encoding='utf-8-sig')
    for needle,label in (
        ('public DXTextBox[] TextBoxes = new DXTextBox[10];','ten filter boxes'),('for (int i = 0; i < 10; i++)','ten-filter constructor loop'),('Size = new Size(150, 20),','filter text size'),('MaxLength = 100,','filter max length'),('Config.HighlightedItems = string.Join(",", TextBoxes.Select(x => x.TextBox.Text));','filter save config'),('GameScene.Game.ReceiveChat(CEnvir.Language.FilterDialogSaveMessage, MessageType.System);','filter save chat'),('SetClientSize(new Size(266, 371));','filter client size'),
    ):req(filter_src,needle,label)
    req(config_src,'public static string HighlightedItems { get; set; } = string.Empty;','checked-in highlighted-items default')
    for needle,label in (
        ('BindTree = new CurrencyTree','currency tree'),('Size = new Size(235, 340),','currency tree size'),('Location = new Point(22, 55),','currency tree location'),('public int HeaderHeight = 22;','currency header height'),('public int CurrencyHeight = 42;','currency item height'),('Change = HeaderHeight,','currency scroll change'),('ScrollBar.Size = new Size(14, Size.Height);','currency scroll width'),('int maxValue = TotalCount - Size.Height;','currency scroll max formula'),('List = GameScene.Game.User.Currencies.OrderBy(x => x.Info.Category).ToList();','runtime currency population'),('CurrencyTree.ListChanged();','runtime currency tree refresh'),('foreach (ClientUserCurrency currency in List.Where(x => x.Info.Category == node.Key))','runtime currency rows'),
    ):req(currency_src,needle,label)
    by={w.get('field'):w for w in spec.get('windows',[])};f=by.get('FilterDropBox');c=by.get('CurrencyBox')
    if not f or not c:raise SystemExit('FilterDropBox/CurrencyBox missing from manifest')
    generated=[x for x in f.get('controls',[]) if str(x.get('name','')).startswith('FilterDropGenerated')]
    if len(generated)!=20:raise SystemExit(f'FilterDrop generated control count drifted: {len(generated)}')
    if sum(x.get('type')=='DXTextBox' for x in generated)!=10 or sum(x.get('type')=='DXLabel' for x in generated)!=10:raise SystemExit('FilterDrop 10 label/10 textbox source expansion drifted')
    state=c.get('currencyTreeSourceState') or {}
    if state.get('scrollBar')!=[221,0,14,340] or state.get('scrollChange')!=22 or state.get('scrollMaxValueNeutral')!=0:raise SystemExit(f'CurrencyTree neutral geometry drifted: {state}')
    f['filterDropSourceAudit']={'passed':True,'filterCount':10,'checkedInHighlightedItems':'','runtimeFilterConfigInvented':False}
    c['currencySourceAudit']={'passed':True,'neutralHeaderCount':0,'neutralCurrencyCount':0,'runtimeCurrenciesInvented':False,'treeBorderAndScrollbarPreserved':True}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Filter/Currency source contract: PASS (10 local filters; CurrencyTree 0 runtime rows)')
if __name__=='__main__':main()
