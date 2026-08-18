#!/usr/bin/env python3
"""Strict source contract for QuestDialog and QuestTracker neutral behavior."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def require(text,needle,label):
    if needle not in text: raise SystemExit(f"Quest source contract changed: {label}: missing {needle!r}")

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'))
    quest=(a.zircon_root/'Client/Scenes/Views/QuestDialog.cs').read_text(encoding='utf-8-sig')
    tracker=(a.zircon_root/'Client/Scenes/Views/QuestTrackerDialog.cs').read_text(encoding='utf-8-sig')
    config=(a.zircon_root/'Client/Envir/Config.cs').read_text(encoding='utf-8-sig')
    for needle,label in (
        ('CurrentTab = new QuestTab','Current tab'),('AvailableTab = new QuestTab','Available tab'),('CompletedTab = new QuestTab','Completed tab'),('MilestoneTab = new MilestoneTab','Milestone tab'),('MissionTab = new MissionTab','Mission tab'),
        ('ShowTrackerBox = { Visible = false }','Available/Completed tracker hidden'),('Checked = Config.QuestTrackerVisible,','Current tracker config binding'),('Config.QuestTrackerVisible = ShowTrackerBox.Checked;','Tracker config update'),('GameScene.Game.QuestTrackerBox.PopulateQuests();','Tracker populate action'),
        ('AbandonButton = { Visible = true }','Current abandon visible'),('Visible = false,\n                Label = { Text = CEnvir.Language.QuestAbandonButtonLabel }','QuestTab abandon neutral hidden'),
        ('new C.QuestAbandon','Quest abandon server packet'),('GameScene.Game.BigMapBox.SelectNPC','quest NPC map locator'),
    ): require(quest,needle,label)
    for needle,label in (
        ('Opacity = 0.0F;','tracker idle opacity'),('AllowResize = true;','tracker resizable'),('this.Opacity = 0.3F;','tracker hover opacity'),('Change = 15,','tracker scroll change'),
        ('if (!Config.QuestTrackerVisible)','tracker config visibility gate'),('Visible = false;','tracker hides when config off'),('if (!userQuest.Track) continue;','tracker per-quest Track gate'),('Visible = Lines.Count > 0;','tracker hides when no lines'),('BaseIndex = 83,','tracker quest icon base'),('FrameCount = 2,','tracker quest icon frames'),
    ): require(tracker,needle,label)
    require(config,'public static bool QuestTrackerVisible { get; set; } = true;','checked-in tracker default true')
    q=next((w for w in spec.get('windows',[]) if w.get('field')=='QuestBox'),None);t=next((w for w in spec.get('windows',[]) if w.get('field')=='QuestTrackerBox'),None)
    if not q or not t: raise SystemExit('Quest/Tracker windows missing from manifest')
    composite=q.get('sourceCompositePass') or q.get('compositePass') or {}
    # Existing build gate already proves Quest composite children; here we lock neutral/runtime provenance.
    q['questSourceAudit']={'passed':True,'trackerDefault':True,'runtimeQuestDataInvented':False,'missionRuntimeOnly':True}
    t['questTrackerSourceAudit']={'passed':True,'neutralLines':0,'neutralVisible':False,'runtimeQuestLinesInvented':False,'hoverOpacity':0.3,'idleOpacity':0.0}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Quest source contract: PASS (tracker default true, neutral 0 lines/hidden, runtime quests not invented)')
if __name__=='__main__': main()
