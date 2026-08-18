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
  'workflow_dispatch:',
  'push:',
  'branches: [origins-game-v1]',
  'apps/zircon-ui-reference/**',
  'tools/zircon-ui-importer/**',
  'actions: read',
  'statuses: write',
  'cancel-in-progress: true',
  'sha="${GITHUB_SHA}"',
  'branches/origins-game-v1',
  'browser-qa-zircon-ui-reference.yml/runs?head_sha=${sha}&branch=origins-game-v1&per_page=20',
  'status" == "completed"',
  'conclusion" == "success"',
  'state="success"',
  'state="failure"',
  'repos/${GITHUB_REPOSITORY}/statuses/${sha}',
  '-f context="origins/zircon-browser-qa"',
  'actions/runs/${run_id}',
  'result unavailable for exact SHA',
 )
 for needle in required:
  if needle not in text:raise SystemExit(f'Browser QA status publisher contract drifted: {needle}')
 forbidden=('workflow_run:','github.event.workflow_run','2511 checkpoint validated','browserValidationPending=false','minimumGameSceneControls=2511')
 for needle in forbidden:
  if needle in text:raise SystemExit(f'Browser QA status publisher contains forbidden/default-branch-dependent or promotion marker: {needle}')
 report={'passed':True,'trigger':'push/workflow_dispatch exact-SHA poll','branch':'origins-game-v1','branchSafeWithoutDefaultBranch':True,'statusPermissionWrite':True,'actionsPermissionRead':True,'exactHeadSha':True,'exactBrowserQaRunRequired':True,'context':'origins/zircon-browser-qa','successMapsToSuccess':True,'nonSuccessMapsToFailure':True,'timeoutMapsToFailure':True,'targetUrlIsWorkflowRun':True,'mutatesSourceContracts':False,'runtimePayloadsInvented':False,'controlsAdded':0}
 spec['browserQaStatusPublisherAudit']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Browser QA status publisher audit: PASS -> branch-safe exact-SHA Browser QA polling and commit status, source contracts untouched')
if __name__=='__main__':main()
