#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    target=Path(__file__).resolve().parents[1]/'augment_ranking_reference.py'
    subprocess.run([sys.executable,str(target),'--spec',str(a.spec),'--zircon-root',str(a.zircon_root)],check=True)
if __name__=='__main__':main()
