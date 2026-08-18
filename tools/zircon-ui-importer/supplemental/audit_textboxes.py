#!/usr/bin/env python3
"""Strict shared DXTextBox / DXNumberTextBox source contract."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def req(text,needle,label):
    if needle not in text:raise SystemExit(f'TextBox source contract changed: {label}: missing {needle!r}')

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    src=(a.zircon_root/'Client/Controls/DXTextBox.cs').read_text(encoding='utf-8-sig')
    communication=(a.zircon_root/'Client/Scenes/Views/CommunicationDialog.cs').read_text(encoding='utf-8-sig')
    guild=(a.zircon_root/'Client/Scenes/Views/GuildDialog.cs').read_text(encoding='utf-8-sig')
    for needle,label in (
        ('public int MaxLength','MaxLength property'),
        ('public bool ReadOnly','ReadOnly property'),
        ('public bool KeepFocus','KeepFocus property'),
        ('public MirTextBox TextBox','MirTextBox bridge property'),
        ('public class MirTextBox : TextBox','native TextBox inheritance'),
        ('protected override void OnTextChanged(EventArgs e)','text-change bridge override'),
        ('Owner.TextureValid = false;','text-change owner texture invalidation'),
        ('Owner.InvalidateParentChildCache();','text-change parent/child cache invalidation'),
    ):req(src,needle,label)
    # Multiline is no longer wrapped as DXTextBox.Multiline. Current Zircon
    # intentionally exposes it through the nested MirTextBox (a WinForms
    # TextBox), and source dialogs set it with nested object initializers.
    req(communication,'TextBox = { Multiline = true, AcceptsReturn = true, }','Communication multiline message editor')
    req(guild,'TextBox = { Multiline = true }','Guild multiline notice editor')
    if 'public bool Multiline' in src:
        raise SystemExit('TextBox source contract changed: DXTextBox.Multiline wrapper was reintroduced; audit must be reviewed')
    controls=[c for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])] for c in w.get('controls',[]) if c.get('type') in ('DXTextBox','DXNumberTextBox')]
    if not controls:raise SystemExit('No DXTextBox/DXNumberTextBox controls in source inventory')
    spec['textBoxSourceAudit']={
        'passed':True,
        'controlCount':len(controls),
        'sourceTypes':sorted({c.get('type') for c in controls}),
        'multilineViaMirTextBox':True,
        'multilineDXWrapperPresent':False,
        'textChangedViaMirTextBoxOverride':True,
        'runtimeValidationInvented':False,
    }
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'TextBox source contract: PASS ({len(controls)} text controls; Multiline via MirTextBox; OnTextChanged bridge)')
if __name__=='__main__':main()
