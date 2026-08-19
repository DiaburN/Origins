#!/usr/bin/env python3
"""Run additive source contracts without editing the core promoter.

Files under tools/zircon-ui-importer/supplemental are auto-discovered in two
phases: augment_*.py first, then audit_*.py. This lets new fidelity modules land
incrementally while the stable core promoter remains conflict-resistant.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--zircon-root',type=Path,required=True)
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    supplemental=here/'supplemental'
    if not supplemental.exists():
        print('No supplemental source contracts directory; nothing to run')
        return
    executed=[]
    for pattern in ('augment_*.py','audit_*.py'):
        for script in sorted(supplemental.glob(pattern)):
            subprocess.run([sys.executable,str(script),'--spec',str(args.spec),'--zircon-root',str(args.zircon_root)],check=True)
            executed.append(script.name)
    print(f'Supplemental source contracts: {len(executed)} PASS -> {", ".join(executed)}')


if __name__=='__main__':main()
