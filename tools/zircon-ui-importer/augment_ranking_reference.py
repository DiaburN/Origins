#!/usr/bin/env python3
"""Promote RankingDialog's deterministic GameScene full-ranking variant.

Current Zircon GameScene constructs RankingDialog(true). Rank rows, selected
player inspect data, online/observable state and search results remain
server/runtime data and stay neutral.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    source_path = args.zircon_root / 'Client/Scenes/Views/RankingDialog.cs'
    game_path = args.zircon_root / 'Client/Scenes/GameScene.cs'
    source = source_path.read_text(encoding='utf-8-sig')
    game = game_path.read_text(encoding='utf-8-sig')

    if not re.search(r'public\s+RankingDialog\s*\(\s*bool\s+fullRanking\s*=\s*false\s*\)', source):
        raise SystemExit('RankingDialog constructor signature changed')
    if 'Index = fullRanking ? 211 : 210;' not in source:
        raise SystemExit('RankingDialog compact/full source indices changed')
    if 'Size = new Size(fullRanking ? 576 : 330, 456);' not in source:
        raise SystemExit('RankingDialog compact/full source size changed')
    if not re.search(r'RankingBox\s*=\s*new\s+RankingDialog\s*\(\s*true\s*\)', game):
        raise SystemExit('GameScene no longer constructs full RankingDialog(true)')

    window = next((w for w in spec.get('windows', []) if w.get('field') == 'RankingBox'), None)
    if not window:
        raise SystemExit('RankingBox missing from source manifest')
    window.setdefault('root', {})['Index'] = '211'
    window['root']['Size'] = 'new Size(576, 456)'
    window['root']['SourceIndexExpression'] = 'fullRanking ? 211 : 210; GameScene RankingDialog(true) => true'
    window['root']['SourceSizeExpression'] = 'new Size(fullRanking ? 576 : 330, 456); GameScene RankingDialog(true) => true'

    line_match = re.search(r'Lines\s*=\s*new\s+RankingLine\s*\[\s*(\d+)\s*\]', source)
    line_count = int(line_match.group(1)) if line_match else None
    window['rankingSourceState'] = {
        'fullRanking': True,
        'sourceIndex': 211,
        'size': [576, 456],
        'selectedRank': None,
        'selectedStartIndex': -1,
        'startIndex': 0,
        'onlineOnly': False,
        'sourceLineCount': line_count,
        'runtimeRanksInvented': False,
        'runtimeInspectInvented': False,
        'runtimeSearchResultsInvented': False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Ranking full source variant promoted: Interface#211 576x456; lines={line_count if line_count is not None else "source expression"}; runtime ranks neutral')


if __name__ == '__main__':
    main()
