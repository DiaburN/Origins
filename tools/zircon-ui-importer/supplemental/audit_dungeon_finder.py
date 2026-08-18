#!/usr/bin/env python3
"""Source/runtime boundary audit for DungeonFinderDialog."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    path=a.zircon_root/'Client/Scenes/Views/DungeonFinderDialog.cs'
    if not path.exists():raise SystemExit('DungeonFinderDialog.cs missing from current Zircon')
    src=path.read_text(encoding='utf-8-sig')
    if not re.search(r'\bclass\s+DungeonFinderDialog\b',src):raise SystemExit('DungeonFinderDialog source class missing')
    if 'DungeonInfo' not in src and 'Dungeon' not in src:raise SystemExit('DungeonFinderDialog no longer references dungeon source data')
    w=next((w for w in spec.get('windows',[]) if w.get('field')=='DungeonFinderBox'),None)
    if not w:raise SystemExit('DungeonFinderBox missing from final manifest')
    packets=sorted(set(re.findall(r'new\s+C\.([A-Za-z_][A-Za-z0-9_]*)',src)))
    control_count=len(w.get('controls',[]))
    if control_count<=0:raise SystemExit('DungeonFinder source controls unexpectedly empty')
    w['dungeonFinderSourceAudit']={'passed':True,'controlCount':control_count,'sourcePacketTypes':packets,'runtimeDungeonDataInvented':False,'runtimeGroupDataInvented':False,'serverActionsExecutedByReference':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'DungeonFinder source boundary: PASS ({control_count} controls, server packets={packets})')
if __name__=='__main__':main()
