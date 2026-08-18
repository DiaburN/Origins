#!/usr/bin/env python3
"""Strict source contract for Ranking, DungeonFinder and Fortune searches."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def require(text,needle,label):
    if needle not in text: raise SystemExit(f'Source search contract changed: {label}: missing {needle!r}')

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
    ): require(ranking,needle,label)
    for needle,label in (
        ('DungeonRows = new DungeonRow[9];','Dungeon 9 rows'),
        ('foreach (InstanceInfo info in Globals.InstanceInfoList.Binding)','Dungeon runtime catalog'),
        ('DungeonSearchResults = new List<InstanceInfo>();','Dungeon local search results'),
        ('JoinButton.Visible = false;','Dungeon join hidden without selection'),
        ('new C.JoinInstance','Dungeon join packet'),
    ): require(dungeon,needle,label)
    for needle,label in (
        ('SearchRows = new FortuneCheckerRow[9];','Fortune 9 rows'),
        ('foreach (ItemInfo info in Globals.ItemInfoList.Binding)','Fortune runtime item catalog'),
        ('SearchResults = new List<ItemInfo>();','Fortune local search results'),
        ('Visible = false;','Fortune source rows hidden'),
        ('new C.FortuneCheck { ItemIndex = ItemInfo.Index }','Fortune check packet'),
    ): require(fortune,needle,label)
    by={w.get('field'):w for w in spec.get('windows',[])}
    if (by['RankingBox'].get('deterministicRankingRows') or {}).get('runtimeRankInfoInvented') is not False: raise SystemExit('Ranking runtime data fabrication contract missing')
    if (by['DungeonFinderBox'].get('deterministicDungeonRows') or {}).get('runtimeInstanceInfoInvented') is not False: raise SystemExit('Dungeon runtime data fabrication contract missing')
    f=by['FortuneCheckerBox'].get('deterministicFortuneRows') or {}
    if f.get('runtimeItemInfoInvented') is not False or f.get('runtimeFortuneInvented') is not False: raise SystemExit('Fortune runtime data fabrication contract missing')
    spec['sourceSearchFlowAudit']={'passed':True,'ranking':'C.RankSearch pending only','dungeonCatalog':'Globals.InstanceInfoList.Binding','fortuneCatalog':'Globals.ItemInfoList.Binding','runtimeResultsInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Source search flow audit: PASS (Ranking/DungeonFinder/Fortune; runtime result data neutral)')
if __name__=='__main__':main()
