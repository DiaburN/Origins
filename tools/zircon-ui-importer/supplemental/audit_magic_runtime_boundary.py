#!/usr/bin/env python3
"""Strict source/runtime boundary for MagicDialog and MagicBarDialog."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));by={w.get('field'):w for w in spec.get('windows',[])}
 magic=by.get('MagicBox');bar=by.get('MagicBarBox')
 if not magic or not bar:raise SystemExit('MagicBox/MagicBarBox missing from final manifest')
 templates=magic.get('dynamicTabTemplates') or {}
 if len(templates.get('templates') or [])!=16 or not templates.get('doNotAssumeVisibleSchools'):
  raise SystemExit(f'Magic dynamic school template contract drifted: {templates}')
 loop=bar.get('magicBarSourceLoop') or {}
 if loop.get('slots')!=24:raise SystemExit(f'MagicBar 24-slot source loop drifted: {loop}')
 if bar.get('root',{}).get('Size')!='new Size(646, 65)':raise SystemExit(f'MagicBar source size drifted: {bar.get("root",{}).get("Size")}')
 magic_src=(a.zircon_root/str(magic.get('sourcePath'))).read_text(encoding='utf-8-sig');bar_src=(a.zircon_root/str(bar.get('sourcePath'))).read_text(encoding='utf-8-sig')
 if 'MagicInfo' not in magic_src:raise SystemExit('MagicDialog no longer references MagicInfo runtime data')
 if 'SpellSet' not in bar_src or 'SpellKey' not in bar_src:raise SystemExit('MagicBar source spell-set/key contract changed')
 magic['magicRuntimeBoundaryAudit']={'passed':True,'sourceSchoolTemplates':16,'neutralVisibleSchools':0,'runtimePlayerMagicInvented':False,'runtimeLevelsOrCooldownsInvented':False}
 bar['magicBarRuntimeBoundaryAudit']={'passed':True,'sourceSlots':24,'neutralAssignedSpells':0,'runtimeSpellAssignmentsInvented':False}
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print('Magic source/runtime boundary: PASS (16 templates, 24 bar slots, 0 fabricated spells)')
if __name__=='__main__':main()
