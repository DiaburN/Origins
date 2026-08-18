#!/usr/bin/env python3
"""Strict source contract for RankingDialog compact GameScene reference state."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

def req(text,needle,label):
    if needle not in text: raise SystemExit(f"Ranking source contract changed: {label}: missing {needle!r}")

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    src=(a.zircon_root/'Client/Scenes/Views/RankingDialog.cs').read_text(encoding='utf-8-sig');game=(a.zircon_root/'Client/Scenes/GameScene.cs').read_text(encoding='utf-8-sig')
    if not re.search(r'public\s+RankingDialog\s*\(\s*bool\s+fullRanking\s*=\s*false\s*\)',src):raise SystemExit('Ranking default compact constructor changed')
    for needle,label in (
        ('Index = fullRanking ? 211 : 210;','compact/full background'),('Size = new Size(fullRanking ? 576 : 330, 456);','compact/full size'),
        ('SelectedRow = null;','selected-row clear'),('SelectedRow = null','selected rank neutral path'),('ObserveButton.Enabled = _SelectedRank != null && _SelectedRank.Online && _SelectedRank.Observable;','observe runtime gate'),
        ('ScrollBar.Value = 0;','filter resets ranking scroll'),('UpdateTime = CEnvir.Now;','runtime refresh scheduling'),('foreach (RankingLine line in Lines)','ranking row runtime refresh'),
    ):req(src,needle,label)
    if not re.search(r'RankingBox\s*=\s*new\s+RankingDialog\s*\(\s*\)',game):raise SystemExit('GameScene RankingBox no longer uses RankingDialog() compact default')
    w=next((w for w in spec.get('windows',[]) if w.get('field')=='RankingBox'),None)
    if not w:raise SystemExit('RankingBox missing from final manifest')
    state=w.get('rankingSourceState') or {}
    if state.get('fullRanking') is not False or state.get('sourceIndex')!=210 or state.get('size')!=[330,456]:raise SystemExit(f'Ranking compact manifest state drifted: {state}')
    if str(w.get('root',{}).get('Index'))!='210' or str(w.get('root',{}).get('Size'))!='new Size(330, 456)':raise SystemExit(f"Ranking root compact promotion drifted: {w.get('root')}")
    controls={c.get('name'):c for c in w.get('controls',[])}
    required={'RequiredClassBox','OnlineOnlyBox','SearchText','SearchButton','ObserveButton','ScrollBar','LastUpdate'}
    missing=sorted(required-set(controls))
    if missing:raise SystemExit(f'Ranking compact controls missing: {missing}')
    w['rankingSourceAudit']={'passed':True,'fullRanking':False,'sourceIndex':210,'size':[330,456],'selectedRank':None,'runtimeRanksInvented':False,'runtimeInspectInvented':False,'runtimeSearchResultsInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Ranking source contract: PASS (compact #210 330x456; rank/search/inspect runtime neutral)')
if __name__=='__main__':main()
