#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, struct
from collections import defaultdict
from pathlib import Path

CLASS_BITS={1:(1,'warrior'),2:(2,'wizard'),4:(3,'taoist'),8:(4,'assassin'),16:(5,'archer'),32:(6,'monk')}
ITEM_TYPES={
  1:('Weapon','weapon',('weapon',)),2:('Armour','armour',('armour',)),4:('Helmet','helmet',('helmet',)),
  5:('Necklace','necklace',('necklace',)),6:('Bracelet','bracelet',('bracelet_left','bracelet_right')),
  7:('Ring','ring',('ring_left','ring_right')),8:('Amulet','amulet',('amulet',)),9:('Belt','belt',('belt',)),
  10:('Boots','boots',('shoes',)),12:('Torch','torch',('torch',))}
STAT_NAMES={0:'MinAC',1:'MaxAC',2:'MinMAC',3:'MaxMAC',4:'MinDC',5:'MaxDC',6:'MinMC',7:'MaxMC',8:'MinSC',9:'MaxSC',10:'Accuracy',11:'Agility',12:'HP',13:'MP',14:'AttackSpeed',15:'Luck',16:'BagWeight',17:'HandWeight',18:'WearWeight',19:'Reflect',20:'Strong',21:'Holy',22:'Freezing',23:'PoisonAttack',30:'MagicResist',31:'PoisonResist',32:'HealthRecovery',33:'SpellRecovery',34:'PoisonRecovery',35:'CriticalRate',36:'CriticalDamage',40:'MaxACRatePercent',41:'MaxMACRatePercent',42:'MaxDCRatePercent',43:'MaxMCRatePercent',44:'MaxSCRatePercent',45:'AttackSpeedRatePercent',46:'HPRatePercent',47:'MPRatePercent',48:'HPDrainRatePercent',100:'ExpRatePercent',101:'ItemDropRatePercent',102:'GoldDropRatePercent',107:'SkillGainMultiplier',108:'AttackBonus'}
CORE=set(range(14))

class R:
  def __init__(self,b): self.b=b; self.p=0
  def rd(self,n):
    x=self.b[self.p:self.p+n]
    if len(x)!=n: raise EOFError(f'EOF @{self.p} need {n}')
    self.p+=n; return x
  def v(self,f): return struct.unpack(f,self.rd(struct.calcsize(f)))[0]
  def i16(self): return self.v('<h')
  def u16(self): return self.v('<H')
  def i32(self): return self.v('<i')
  def u32(self): return self.v('<I')
  def u8(self): return self.v('<B')
  def bo(self): return self.u8()!=0
  def s(self):
    n=0; sh=0
    while True:
      q=self.u8(); n|=(q&127)<<sh
      if not q&128: break
      sh+=7
      if sh>=35: raise ValueError('bad .NET string length')
    return self.rd(n).decode('utf-8')

def skip_safe(r): r.i32();r.i32();r.u16();r.bo()
def skip_respawn(r,v):
  r.i32();r.i32();r.i32();r.u16();r.u16();r.u16();r.u8();r.s()
  if v>67: r.u16();r.i32();r.bo();r.u16()
def skip_move(r,v):
  r.i32();r.i32();r.i32();r.i32();r.i32();r.bo();r.bo()
  if v>=69:r.i32()
  if v>=95:r.bo();r.i32()
def skip_mine(r): r.i32();r.i32();r.u16();r.u8()
def skip_map(r,v):
  r.i32();r.s();r.s();r.u16();r.u8();r.u16()
  for _ in range(r.i32()): skip_safe(r)
  for _ in range(r.i32()): skip_respawn(r,v)
  for _ in range(r.i32()): skip_move(r,v)
  r.bo();r.bo();r.s()
  for _ in range(9): r.bo() # NoRandom..NoNames
  r.bo()                     # Fight
  r.bo();r.i32();r.bo();r.i32();r.u8()
  for _ in range(r.i32()): skip_mine(r)
  r.u8();r.bo();r.bo();r.bo();r.u16()
  if v>=78:r.bo()
  if v>=79:r.bo()
  if v>=110:r.u16()
  if v>=111:r.bo();r.u8()
  if v>=114:
    for _ in range(5):r.bo()
    r.i32();r.bo();r.bo();r.i32()

def stats(r,v):
  if v<=84: raise ValueError('modern Crystal DB (>84) required')
  n=r.i32()
  if not 0<=n<=1000: raise ValueError(f'bad stat count {n} @{r.p}')
  return {r.u8():r.i32() for _ in range(n)}
def item(r,v):
  x={'index':r.i32(),'name':r.s(),'type':r.u8(),'grade':r.u8(),'required_type':r.u8(),'required_class':r.u8(),'required_gender':r.u8(),'set_id':r.u8(),'shape':r.i16(),'weight':r.u8(),'light':r.u8(),'required_amount':r.u8(),'image':r.u16(),'durability':r.u16()}
  x['stack_size']=r.u16() if v>84 else r.u32();x['price']=r.u32()
  if v<=84: raise ValueError('legacy DB not supported')
  x['start_item']=r.bo();x['effect']=r.u8();x['flags']=r.u8();x['bind']=r.i16();x['unique']=r.i16();x['random_stats_id']=r.u8();x['can_fast_run']=r.bo();x['can_awakening']=r.bo();x['slots']=r.u8() if v>83 else 0;x['stats']=stats(r,v);x['tooltip']=r.s() if r.bo() else ''
  return x

def enums(path,name):
  t=path.read_text(encoding='utf-8-sig',errors='replace');m=re.search(rf'public\s+enum\s+{name}(?:\s*:\s*\w+)?\s*\{{(.*?)\n\}}',t,re.S)
  if not m:return {}
  out={};cur=-1
  for raw in m.group(1).splitlines():
    z=raw.split('//',1)[0].strip().rstrip(',')
    if not z:continue
    if '=' in z:
      k,val=map(str.strip,z.split('=',1))
      try:cur=int(val,0)
      except ValueError:continue
    else:k=z;cur+=1
    if re.fullmatch(r'[A-Za-z_]\w*',k):out[cur]=k
  return out

def q(s):return "'"+str(s).replace("'","''")+"'"
def class_list(mask):
  if mask in (0,31,63):return []
  return [v for bit,v in CLASS_BITS.items() if mask&bit]

def parse(path):
  r=R(path.read_bytes());v=r.i32();cv=r.i32()
  if v<=84:raise ValueError(f'unsupported DB v{v}')
  h={'version':v,'custom_version':cv,'map_index':r.i32(),'item_index':r.i32(),'monster_index':r.i32(),'npc_index':r.i32(),'quest_index':r.i32()}
  if v>=63:h['gameshop_index']=r.i32()
  if v>=66:h['conquest_index']=r.i32()
  if v>67:h['respawn_index']=r.i32()
  h['map_count']=r.i32()
  for _ in range(h['map_count']):skip_map(r,v)
  h['item_count']=r.i32();xs=[item(r,v) for _ in range(h['item_count'])];h['items_end_offset']=r.p
  return h,xs

def equipment(xs,names):
  out=[]
  for x in xs:
    ti=ITEM_TYPES.get(x['type']);cl=class_list(x['required_class'])
    if not ti or not cl:continue
    typ,fam,slots=ti;allstats={STAT_NAMES.get(k,f'Stat{k}'):v for k,v in x['stats'].items() if v}
    y=dict(x,type_name=typ,family=fam,equip_slots=list(slots),classes=[{'id':i,'code':c} for i,c in cl],required_type_name=names['RequiredType'].get(x['required_type'],f'RequiredType{x["required_type"]}'),grade_name=names['ItemGrade'].get(x['grade'],f'Grade{x["grade"]}'),set_name=names['ItemSet'].get(x['set_id'],f'Set{x["set_id"]}'),core_stats={STAT_NAMES.get(k,f'Stat{k}'):v for k,v in x['stats'].items() if k in CORE and v},extra_stats_preserved={STAT_NAMES.get(k,f'Stat{k}'):v for k,v in x['stats'].items() if k not in CORE and v},all_stats=allstats)
    out.append(y)
  return out

def report(h,xs):
  d=defaultdict(lambda:{'items':0,'level_items':0,'max_required_level':None,'families':defaultdict(int)})
  monk=0
  for x in xs:
    for c in x['classes']:
      a=d[c['code']];a['items']+=1;a['families'][x['family']]+=1
      if x['required_type_name'].lower()=='level':a['level_items']+=1;a['max_required_level']=max(a['max_required_level'] or 0,x['required_amount'])
      if c['code']=='monk':monk+=1
  cs={}
  for c in ('warrior','wizard','taoist','assassin','archer','monk'):
    a=d[c];cs[c]={'items':a['items'],'level_items':a['level_items'],'max_required_level':a['max_required_level'],'families':dict(sorted(a['families'].items()))}
  return {'database':h,'class_specific_equipment_items':len(xs),'monk_items_detected_in_source_db':monk,'classes':cs,'policy':{'identity':'Crystal original names and requirements','runtime':'Zircon-style ORIGINS item system','stats':'flat core source stats; extra source stats preserved only','generic_items':'Zircon catalogue phase'}}

def sql(xs,commit):
  repo='Suprcode/Crystal.Database';path='Jev/Server.MirDB';o=['BEGIN;']
  for x in xs:
    key=f"crystal.item.{x['index']}";meta={'crystal_set_id':x['set_id'],'crystal_set_name':x['set_name'],'crystal_effect':x['effect'],'source_stats_all':x['all_stats'],'extra_stats_preserved':x['extra_stats_preserved']}
    vals=[q(key),q(x['name']),q(x['type_name']),str(x['required_class']),str(x['required_gender']),q(x['required_type_name']),str(x['required_amount']),str(x['shape']),str(x['image']),str(x['durability']),str(x['price']),str(x['weight']),str(x['stack_size']),'true' if x['start_item'] else 'false',q(x['grade_name']),q('crystal'),str(x['index']),q(repo),q(path),q(commit),q('restricted'),q('zircon'),q(json.dumps(meta,separators=(',',':')))+'::jsonb']
    o.append('INSERT INTO content.item_definitions (game_key,item_name,item_type,required_class_mask,required_gender,required_type,required_amount,shape,image_index,durability,price,weight,stack_size,start_item,rarity,source_system,source_item_id,source_repo,source_path,source_commit,class_restriction_mode,runtime_source,metadata) VALUES ('+','.join(vals)+') ON CONFLICT (game_key) DO NOTHING;')
    for s,a in sorted(x['core_stats'].items()):o.append(f"INSERT INTO content.item_stats SELECT id,{q(s)},{int(a)} FROM content.item_definitions WHERE game_key={q(key)} ON CONFLICT (item_definition_id,stat_code) DO UPDATE SET amount=EXCLUDED.amount;")
    for c in x['classes']:o.append(f"INSERT INTO content.item_allowed_classes(item_definition_id,class_id,source_system,source_item_id,source_repo,source_path,source_commit) SELECT id,{c['id']},'crystal',{x['index']},{q(repo)},{q(path)},{q(commit)} FROM content.item_definitions WHERE game_key={q(key)} ON CONFLICT DO NOTHING;")
    for sl in x['equip_slots']:o.append(f"INSERT INTO content.item_equip_slots SELECT id,{q(sl)} FROM content.item_definitions WHERE game_key={q(key)} ON CONFLICT DO NOTHING;")
  g=defaultdict(list)
  for x in xs:
    for c in x['classes']:g[(c['id'],x['family'])].append(x)
  for (cid,fam),arr in sorted(g.items()):
    arr.sort(key=lambda z:(0 if z['required_type_name'].lower()=='level' else 1,z['required_amount'],z['index']))
    for tier,x in enumerate(arr,1):
      key=f"crystal.item.{x['index']}";o.append(f"INSERT INTO content.equipment_progression(class_id,equipment_family,tier_order,item_definition_id,original_name,required_type,required_amount,source_system,source_item_id,source_set_id,source_repo,source_path,source_commit) SELECT {cid},{q(fam)},{tier},id,{q(x['name'])},{q(x['required_type_name'])},{x['required_amount']},'crystal',{x['index']},{x['set_id']},{q(repo)},{q(path)},{q(commit)} FROM content.item_definitions WHERE game_key={q(key)} ON CONFLICT DO NOTHING;")
  sets=defaultdict(list)
  for x in xs:
    if x['set_id']:sets[(x['set_id'],x['set_name'])].append(x)
  for (sid,sname),arr in sorted(sets.items()):
    sk=f'crystal.set.{sid}';o.append(f"INSERT INTO content.item_set_definitions(game_key,set_name,source_system,source_set_id,source_repo,source_path,source_commit) VALUES ({q(sk)},{q(sname)},'crystal',{sid},{q(repo)},{q(path)},{q(commit)}) ON CONFLICT (game_key) DO NOTHING;")
    for x in arr:o.append(f"INSERT INTO content.item_set_members SELECT s.id,i.id FROM content.item_set_definitions s,content.item_definitions i WHERE s.game_key={q(sk)} AND i.game_key={q('crystal.item.'+str(x['index']))} ON CONFLICT DO NOTHING;")
  o+=['COMMIT;',''];return '\n'.join(o)

def main():
  a=argparse.ArgumentParser();a.add_argument('--db',type=Path,required=True);a.add_argument('--enums',type=Path,required=True);a.add_argument('--source-commit',required=True);a.add_argument('--out-json',type=Path,required=True);a.add_argument('--out-sql',type=Path,required=True);z=a.parse_args()
  h,raw=parse(z.db);names={n:enums(z.enums,n) for n in ('RequiredType','ItemGrade','ItemSet')};xs=equipment(raw,names);rep=report(h,xs);rep['items']=xs
  z.out_json.parent.mkdir(parents=True,exist_ok=True);z.out_json.write_text(json.dumps(rep,indent=2,ensure_ascii=False),encoding='utf-8');z.out_sql.write_text(sql(xs,z.source_commit),encoding='utf-8')
  print(json.dumps({'db_version':h['version'],'source_items':h['item_count'],'class_equipment':len(xs),'classes':rep['classes'],'monk_items_detected':rep['monk_items_detected_in_source_db']},indent=2))
if __name__=='__main__':main()
