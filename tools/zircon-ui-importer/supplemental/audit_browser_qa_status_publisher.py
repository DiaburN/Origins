#!/usr/bin/env python3
"""Strict contract for publishing Browser QA conclusion to the exact commit SHA."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));root=Path(__file__).resolve().parents[3];path=root/'.github/workflows/publish-zircon-browser-qa-status.yml'
 if not path.exists():raise SystemExit('Browser QA status publisher workflow missing')
 text=path.read_text(encoding='utf-8')
 required=(
  'name: Publish Zircon Browser QA status',
  'workflows: ["Browser QA Zircon UI reference"]',
  'types: [completed]',
  'statuses: write',
  "github.event.workflow_run.head_branch == 'origins-game-v1'",
  'QA_SHA: ${{ github.event.workflow_run.head_sha }}',
  'QA_CONCLUSION: ${{ github.event.workflow_run.conclusion }}',
  'QA_URL: ${{ github.event.workflow_run.html_url }}',
  'if [[ "$QA_CONCLUSION" == "success" ]]',
  'state="success"',
  'state="failure"',
  'repos/${GITHUB_REPOSITORY}/statuses/${QA_SHA}',
  '-f context="origins/zircon-browser-qa"',
  '-f target_url="$QA_URL"',
 )
 for needle in required:
  if needle not in text:raise SystemExit(f'Browser QA status publisher contract drifted: {needle}')
 forbidden=('2511 checkpoint validated','browserValidationPending=false','minimumGameSceneControls=2511')
 for needle in forbidden:
  if needle in text:raise SystemExit(f'status publisher must report CI conclusion only, not mutate/promote source contracts: {needle}')
 report={'passed':True,'trigger':'Browser QA Zircon UI reference completed','branch':'origins-game-v1','statusPermissionWrite':True,'exactHeadSha':True,'context':'origins/zircon-browser-qa','successMapsToSuccess':True,'nonSuccessMapsToFailure':True,'targetUrlIsWorkflowRun':True,'mutatesSourceContracts':False,'runtimePayloadsInvented':False,'controlsAdded':0}
 spec['browserQaStatusPublisherAudit']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Browser QA status publisher audit: PASS -> exact SHA success/failure status, source contracts untouched')
if __name__=='__main__':main()
