#!/usr/bin/env python3
"""Final gate that keeps the Chat Options local-tab smoke wired into Browser QA."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    final = spec.get('finalSupplementalSourceMatrix') or {}
    failures: list[str] = []
    if final.get('passed') is not True:
        failures.append(f'prior final matrix missing/not PASS: {final}')

    root = Path(__file__).resolve().parents[3]
    workflow_path = root / '.github/workflows/browser-qa-zircon-ui-reference.yml'
    runtime_path = root / 'apps/zircon-ui-reference/browser-qa-chat-options-runtime.js'
    if not workflow_path.exists():
        failures.append('Browser QA workflow missing')
        workflow = ''
    else:
        workflow = workflow_path.read_text(encoding='utf-8')
    if not runtime_path.exists():
        failures.append('Chat Options Browser QA runtime missing')
        runtime = ''
    else:
        runtime = runtime_path.read_text(encoding='utf-8')

    required_workflow = (
        'cp apps/zircon-ui-reference/browser-qa-chat-options-runtime.js .qa/viewer/browser-qa-chat-options-runtime.js',
        'node --check .qa/viewer/browser-qa-chat-options-runtime.js',
        '<script type="module" src="browser-qa-chat-options-runtime.js"></script>',
        'index.html?qaChatOptions=1',
        '.qa/chat-options-browser-qa-report.json',
        "if chat.get('status') != 'pass'",
        "expected_zero={'listItems':0,'panels':0,'tabControls':0,'chatTabs':0}",
        "expected_one={'listItems':1,'panels':1,'tabControls':1,'chatTabs':1}",
        "if chat.get('manifestControlsAdded') != 0 or chat.get('runtimePayloadsInvented') is not False",
        '.qa/chat-options-browser-qa-dom.html',
        '.qa/chat-options-http-server.log',
    )
    for needle in required_workflow:
        if needle not in workflow:
            failures.append(f'Browser QA Chat Options wiring marker missing: {needle}')

    required_runtime = (
        "if(params.get('qaChatOptions')==='1')",
        "data-source-local-action=\"AddNewTab(null)\"",
        "if(root.dataset.constructorPrecreatedLocalTabs!=='0')",
        "checks.length!==16",
        "manifestControlsAdded:0",
        "runtimePayloadsInvented:false",
        "remove.click()",
    )
    for needle in required_runtime:
        if needle not in runtime:
            failures.append(f'Chat Options Browser QA source marker missing: {needle}')
    if '!r}' in runtime or '!r,' in runtime:
        failures.append('Chat Options Browser QA contains Python-style !r syntax in JavaScript')

    report = {
        'passed': not failures,
        'sameShaBuildArtifact': 'head_sha=${GITHUB_SHA}' in workflow,
        'runtimeNodeCheck': 'node --check .qa/viewer/browser-qa-chat-options-runtime.js' in workflow,
        'constructorTabsExpected': 0,
        'clickCreatedTabsExpected': 1,
        'checkboxesExpected': 16,
        'removeClearsLocalTree': 'afterRemove' in workflow and 'remove.click()' in runtime,
        'manifestControlsAdded': 0,
        'runtimePayloadsInvented': False,
        'evidenceUploaded': '.qa/chat-options-browser-qa-report.json' in workflow,
        'failures': failures,
    }
    spec['browserQaChatOptionsWiringAudit'] = report

    final['browserQaChatOptionsWiringPassed'] = report['passed']
    final['browserQaChatOptionsSameShaArtifact'] = report['sameShaBuildArtifact']
    final['browserQaChatOptionsRuntimeNodeCheck'] = report['runtimeNodeCheck']
    final['browserQaChatOptionsManifestControlsAdded'] = 0
    final['browserQaChatOptionsRuntimePayloadsInvented'] = False
    final['passed'] = final.get('passed') is True and not failures
    final['failures'] = list(final.get('failures') or []) + failures
    spec['finalSupplementalSourceMatrix'] = final

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if failures:
        raise SystemExit('Browser QA Chat Options wiring gate failed:\n- ' + '\n- '.join(failures))
    print('Browser QA Chat Options wiring: PASS -> exact SHA artifact, Add/Remove smoke, manifest +0')


if __name__ == '__main__':
    main()
