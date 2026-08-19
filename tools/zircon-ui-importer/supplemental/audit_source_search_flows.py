#!/usr/bin/env python3
"""Strict source contract for Ranking, DungeonFinder and Fortune searches."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def require(text,needle,label):
    if needle not in text: raise SystemExit(f'Source search contract changed: {label}: missing {needle!r}')

def combo(window,name):
    c=next((x for x in window.get('controls',[]) if x.get('name')==name and x.get('type')=='DXComboBox'),None)
    if not c: raise SystemExit(f'Source search combo missing: {window.get("field")}.{name}')
    return c

def labels(control): return [str(x.get('label') or '') for x in control.get('comboOptions',[])]

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'));root=a.zircon_root
    ranking=(root/'Client/Scenes/Views/RankingDialog.cs').read_text(encoding='utf-8-sig')
    dungeon=(root/'Client/Scenes/Views/DungeonFinderDialog.cs').read_text(encoding='utf-8-sig')
    fortune=(root/'Client/Scenes/Views/FortuneCheckerDialog.cs').read_text(encoding='utf-8-sig')
    for needle,label in (
        ('SearchButton.Enabled = !string.IsNullOrEmpty(SearchText.TextBox.Text);','Ranking text enables Search'),
        ('Enabled = false','Ranking Search initial disabled'),
        ('new C.RankSearch { Name = SearchText.TextBox.Text }','Ranking search packet'),
        ('FilterClass = (RequiredClass?)RequiredClassBox.SelectedItem ?? RequiredClass.All;','Ranking class filter'),
        ('OnlineOnly = OnlineOnlyBox.Checked;','Ranking online filter'),
        ('RequiredClassBox.ListBox.SelectItem((RequiredClass)Config.RankingClass);','Ranking source class selection'),
    ): require(ranking,needle,label)
    for needle,label in (
        ('DungeonRows = new DungeonRow[9];','Dungeon 9 rows'),
        ('foreach (InstanceInfo info in Globals.InstanceInfoList.Binding)','Dungeon runtime catalog'),
        ('DungeonSearchResults = new List<InstanceInfo>();','Dungeon local search results'),
        ('JoinButton.Visible = false;','Dungeon join hidden without selection'),
        ('new C.JoinInstance','Dungeon join packet'),
        ('SortBox.ListBox.SelectItem(DungeonFinderSort.Name);','Dungeon source sort selection'),
    ): require(dungeon,needle,label)
    for needle,label in (
        ('SearchRows = new FortuneCheckerRow[9];','Fortune 9 rows'),
        ('foreach (ItemInfo info in Globals.ItemInfoList.Binding)','Fortune runtime item catalog'),
        ('SearchResults = new List<ItemInfo>();','Fortune local search results'),
        ('Visible = false;','Fortune source rows hidden'),
        ('new C.FortuneCheck { ItemIndex = ItemInfo.Index }','Fortune check packet'),
        ('ItemTypeBox.ListBox.SelectItem(null);','Fortune source All selection'),
    ): require(fortune,needle,label)
    by={w.get('field'):w for w in spec.get('windows',[])}
    if (by['RankingBox'].get('deterministicRankingRows') or {}).get('runtimeRankInfoInvented') is not False: raise SystemExit('Ranking runtime data fabrication contract missing')
    if (by['DungeonFinderBox'].get('deterministicDungeonRows') or {}).get('runtimeInstanceInfoInvented') is not False: raise SystemExit('Dungeon runtime data fabrication contract missing')
    f=by['FortuneCheckerBox'].get('deterministicFortuneRows') or {}
    if f.get('runtimeItemInfoInvented') is not False or f.get('runtimeFortuneInvented') is not False: raise SystemExit('Fortune runtime data fabrication contract missing')

    rank_combo=combo(by['RankingBox'],'RequiredClassBox')
    rank_labels=labels(rank_combo)
    if rank_labels != ['All','Warrior','Wizard','Taoist','Assassin']:
        raise SystemExit(f'Ranking class options drifted: {rank_labels}')
    if str(rank_combo.get('comboSelectedExpression') or '').replace(' ','') != '(RequiredClass)Config.RankingClass'.replace(' ',''):
        raise SystemExit(f'Ranking class source selection expression missing: {rank_combo.get("comboSelectedExpression")}')

    dungeon_combo=combo(by['DungeonFinderBox'],'SortBox')
    if labels(dungeon_combo) != ['Name','Level','Player Count']:
        raise SystemExit(f'DungeonFinder sort options drifted: {labels(dungeon_combo)}')
    if dungeon_combo.get('comboSelectedOptionIndex') != 0:
        raise SystemExit(f'DungeonFinder sort default is not Name/index0: {dungeon_combo.get("comboSelectedOptionIndex")}')

    fortune_combo=combo(by['FortuneCheckerBox'],'ItemTypeBox')
    fortune_labels=labels(fortune_combo)
    if len(fortune_labels) != 35 or fortune_labels[0] != 'All':
        raise SystemExit(f'Fortune ItemType options drifted: count={len(fortune_labels)} first={fortune_labels[:3]}')
    if fortune_combo.get('comboSelectedOptionIndex') != 0:
        raise SystemExit(f'Fortune ItemType default is not All/index0: {fortune_combo.get("comboSelectedOptionIndex")}')

    spec['sourceSearchFlowAudit']={
        'passed':True,'ranking':'C.RankSearch pending only','rankingClassOptions':5,
        'dungeonCatalog':'Globals.InstanceInfoList.Binding','dungeonSortOptions':3,
        'fortuneCatalog':'Globals.ItemInfoList.Binding','fortuneItemTypeOptions':35,
        'runtimeResultsInvented':False,
    }
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Source search flow audit: PASS (Ranking 5, Dungeon 3, Fortune 35 options; runtime result data neutral)')
if __name__=='__main__':main()
