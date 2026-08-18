#!/usr/bin/env python3
"""Strict source contract for the exact-artifact Browser QA workflow."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));root=Path(__file__).resolve().parents[3];path=root/'.github/workflows/browser-qa-zircon-ui-reference.yml'
 if not path.exists():raise SystemExit('Browser QA workflow missing')
 text=path.read_text(encoding='utf-8')
 required=(
  'name: Browser QA Zircon UI reference',
  'build-zircon-ui-reference.yml/runs?head_sha=${GITHUB_SHA}',
  'zircon-ui-reference-complete',
  'browser-qa-runtime.js',
  'browser-qa-window-runtime.js',
  '#browser-qa-result',
  "report.get('status') != 'pass'",
  "report.get('testedWindows') != 80",
  "int(report.get('gameControlCount') or 0) < 2511",
  "int(report.get('nestedControlCount') or 0) < 143",
  "floor.get('gameScene') != 2511",
  "floor.get('browserValidationPending') is not True",
  "final.get('minimumGameSceneControls') != 2507",
  "final.get('latestSourceAuditedGameSceneFloor') != 2511",
  "final.get('browserValidatedFloorPending') is not True",
  "bigmap.get(key) != value",
  'zircon-ui-browser-qa-${{ github.sha }}',
 )
 for needle in required:
  if needle not in text:raise SystemExit(f'Browser QA workflow contract drifted: {needle}')
 forbidden=("< 1634","< 1946","< 2053","< 2284","< 2466","minimumGameSceneControls') != 2511")
 for needle in forbidden:
  if needle in text:raise SystemExit(f'Browser QA contains obsolete/premature floor contract: {needle}')
 spec['browserQaWorkflowAudit']={'passed':True,'exactShaBuildArtifactRequired':True,'artifactName':'zircon-ui-reference-complete','expectedWindows':80,'sourceGameFloor':2511,'nestedFloor':143,'priorBrowserCheckpoint':2507,'checkpointPromotionPendingUntilPass':True,'bigMapSidePanelContractRequired':True,'failureEvidenceUploaded':True,'runtimePayloadsInvented':False};a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Browser QA workflow audit: PASS -> exact SHA artifact, 80 windows, 2511 source floor, 2507 prior checkpoint pending Chrome')
if __name__=='__main__':main()
