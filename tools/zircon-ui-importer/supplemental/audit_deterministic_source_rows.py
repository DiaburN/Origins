#!/usr/bin/env python3
"""Strict gate for deterministic source-created row composites."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def win(spec,field):
    w=next((x for x in spec.get('windows',[]) if x.get('field')==field),None)
    if not w: raise SystemExit(f'{field} missing')
    return w

def props(c): return c.get('properties') or {}

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'))
    report=spec.get('deterministicSourceRowPass') or {}
    if report.get('runtimePayloadsInvented') is not False:
        raise SystemExit(f'Deterministic row provenance broken: {report}')
    if not (312 <= int(report.get('controlsAdded',0)) <= 314):
        raise SystemExit(f'Deterministic row expansion count drifted: {report}')

    ranking=win(spec,'RankingBox'); by={c.get('name'):c for c in ranking.get('controls',[])}
    if ranking.get('deterministicRankingRows') != {'searchRows':1,'rankingRows':11,'rowSize':[288,22],'rowStep':23,'regularRowsVisible':False,'runtimeRankInfoInvented':False}:
        raise SystemExit(f'Ranking deterministic row contract drifted: {ranking.get("deterministicRankingRows")}')
    rows=[by.get('RankingSearchLineSource')]+[by.get(f'RankingLineSource{i:02d}') for i in range(1,12)]
    if any(r is None for r in rows): raise SystemExit('Ranking 12 source-created rows not fully expanded')
    if props(rows[0]).get('Visible')!='true' or any(props(r).get('Visible')!='false' for r in rows[1:]):
        raise SystemExit('Ranking source row visibility state drifted')
    for r in rows:
        name=r['name']
        children=[by.get(f'{name}OnlineImage'),by.get(f'{name}RankLabel'),by.get(f'{name}LevelLabel'),by.get(f'{name}NameLabel'),by.get(f'{name}ChangeLabel')]
        if any(c is None for c in children): raise SystemExit(f'RankingLine composite children incomplete: {name}')
        if any((c.get('resolvedText') or '') for c in children if c.get('type')=='DXLabel'):
            raise SystemExit(f'Fabricated neutral ranking text: {name}')

    dungeon=win(spec,'DungeonFinderBox'); by={c.get('name'):c for c in dungeon.get('controls',[])}
    contract=dungeon.get('deterministicDungeonRows') or {}
    if contract.get('rowCount')!=9 or contract.get('neutralVisible') is not False or contract.get('runtimeInstanceInfoInvented') is not False:
        raise SystemExit(f'Dungeon deterministic row contract drifted: {contract}')
    for i in range(1,10):
        name=f'DungeonRowSource{i:02d}';row=by.get(name)
        if row is None or props(row).get('Visible')!='false': raise SystemExit(f'Dungeon neutral row missing/visible: {name}')
        for suffix in ('NameLabel','TypeLabel','LevelLabel','CountLabel','FavouriteImage'):
            if by.get(f'{name}{suffix}') is None: raise SystemExit(f'Dungeon row child missing: {name}{suffix}')
        for suffix in ('NameLabel','TypeLabel','LevelLabel','CountLabel'):
            if by[f'{name}{suffix}'].get('resolvedText') not in ('',None): raise SystemExit(f'Fabricated Dungeon data text: {name}{suffix}')

    fortune=win(spec,'FortuneCheckerBox'); by={c.get('name'):c for c in fortune.get('controls',[])}
    contract=fortune.get('deterministicFortuneRows') or {}
    if contract.get('rowCount')!=9 or contract.get('neutralVisible') is not False or contract.get('runtimeItemInfoInvented') is not False or contract.get('runtimeFortuneInvented') is not False:
        raise SystemExit(f'Fortune deterministic row contract drifted: {contract}')
    if contract.get('exactIntegerCellLocation') != [9,9] or contract.get('checkButtonConstructorEnabled') is not True:
        raise SystemExit(f'Fortune exact constructor postfix missing: {contract}')
    for i in range(1,10):
        name=f'FortuneRowSource{i:02d}';row=by.get(name);cell=by.get(f'{name}ItemCell');button=by.get(f'{name}CheckButton')
        if row is None or props(row).get('Visible')!='false': raise SystemExit(f'Fortune neutral row missing/visible: {name}')
        if props(cell).get('Location')!='new Point(9, 9)' or props(button).get('Enabled')!='true': raise SystemExit(f'Fortune exact child state drifted: {name}')
        for suffix in ('ItemCell','NameLabel','CountLabelLabel','CountLabel','ProgressLabelLabel','ProgressLabel','DateLabelLabel','DateLabel','CheckButton'):
            if by.get(f'{name}{suffix}') is None: raise SystemExit(f'Fortune row child missing: {name}{suffix}')
        for suffix in ('NameLabel','CountLabel','ProgressLabel','DateLabel'):
            if by[f'{name}{suffix}'].get('resolvedText') not in ('',None): raise SystemExit(f'Fabricated Fortune runtime text: {name}{suffix}')

    big=win(spec,'BigMapBox'); by={c.get('name'):c for c in big.get('controls',[])}
    contract=big.get('deterministicBigMapRows') or {}
    if contract.get('npcRows')!=24 or contract.get('monsterRows')!=24 or contract.get('neutralVisible') is not False:
        raise SystemExit(f'BigMap deterministic row contract drifted: {contract}')
    if any(contract.get(k) is not False for k in ('runtimeMapInfoInvented','runtimeNPCsInvented','runtimeMonstersInvented')):
        raise SystemExit(f'BigMap runtime payload fabrication contract broken: {contract}')
    for prefix in ('BigMapNPCRowSource','BigMapMonsterRowSource'):
        for i in range(1,25):
            name=f'{prefix}{i:02d}';row=by.get(name);label=by.get(f'{name}NameLabel')
            if row is None or label is None: raise SystemExit(f'BigMap row composite missing: {name}')
            if props(row).get('Visible')!='false' or label.get('resolvedText') not in ('',None): raise SystemExit(f'BigMap neutral row leaked runtime data: {name}')
    for name in ('NPCScrollBar','MonsterScrollBar'):
        sb=by.get(name)
        if sb is None or sb.get('type')!='DXVScrollBar': raise SystemExit(f'BigMap source scrollbar missing: {name}')
        if props(sb).get('Change')!='1': raise SystemExit(f'BigMap source scrollbar Change drifted: {name}')

    spec['deterministicSourceRowAudit']={'passed':True,'rankingRows':12,'dungeonRows':9,'fortuneRows':9,'bigMapRows':48,'runtimePayloadsInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Deterministic source row audit: PASS (12 Ranking, 9 Dungeon, 9 Fortune, 48 BigMap rows)')
if __name__=='__main__':main()
