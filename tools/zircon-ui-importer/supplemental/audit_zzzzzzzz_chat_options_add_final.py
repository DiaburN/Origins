#!/usr/bin/env python3
"""Final bridge for source-local ChatOptions AddNewTab runtime."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));final=spec.get('finalSupplementalSourceMatrix') or {};audit=spec.get('chatOptionsAddLocalRuntimeAudit') or {};fail=[]
 if final.get('passed') is not True:fail.append(f'prior final matrix missing/not PASS: {final}')
 expected={'passed':True,'constructorTabs':0,'clickCreatedStateOnly':True,'tabControlSize':[200,200],'resizeBuffer':9,'usesAssetSizedButtonPieces':True,'chatMessagesInvented':False,'userDataInvented':False,'serverDataInvented':False,'manifestControlsAdded':0}
 for key,value in expected.items():
  if audit.get(key)!=value:fail.append(f'Chat Options local Add contract drifted: {key}={audit.get(key)!r}, expected {value!r}')
 nested=audit.get('nestedChatTabStructure') or []
 if nested!=['DXVScrollBar','DXControl(TextPanel)','DXImageControl(AlertIcon hidden)']:fail.append(f'ChatTab nested local structure drifted: {nested}')
 final['chatOptionsLocalAddRuntimePassed']=audit.get('passed') is True;final['chatOptionsConstructorTabs']=audit.get('constructorTabs');final['chatOptionsLocalManifestControlsAdded']=audit.get('manifestControlsAdded');final['chatOptionsLocalRuntimePayloadsInvented']=False;final['passed']=final.get('passed') is True and not fail;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Final Chat Options local Add runtime contract failed:\n- '+'\n- '.join(fail))
 print('Final Chat Options local Add runtime: PASS -> constructor 0, click-created local state only, manifest +0')
if __name__=='__main__':main()
