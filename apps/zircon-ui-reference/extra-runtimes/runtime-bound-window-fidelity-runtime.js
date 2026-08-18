// Shared source/runtime boundary for dialogs whose meaningful payload only exists
// with live player/item/server state. Static source chrome/labels remain intact;
// only unresolved runtime labels/items are neutralized. No sample data is added.
const stage=document.querySelector('#stage');
let spec=null;
const POLICIES={
  'edit-character':{data:'runtime player appearance/customization state',server:'character edit/update packet'},
  'fortune-checker':{data:'runtime linked item + fortune information',server:'NPC fortune/check action'},
  'bundle':{data:'runtime bundle ClientUserItem/content',server:'bundle action'},
  'loot-box':{data:'runtime loot-box ClientUserItem/reward result',server:'loot-box action'},
  'fishing':{data:'runtime fishing rod/cast/fish state',server:'fishing action'},
  'fishing-catch':{data:'runtime fish/catch pointer state',server:'fishing catch result'},
  'horse-tame':{data:'runtime horse-tame progress/result',server:'horse tame action'},
  'milestone-achieved':{data:'runtime milestone/achievement payload',server:null},
  'caption':{data:'runtime map/location caption text',server:null},
};
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function exactLiteral(raw){const text=String(raw??'').trim();if(text==='string.Empty')return '';const m=text.match(/^"((?:\\.|[^"\\])*)"$/);if(!m)return null;try{return JSON.parse(text)}catch{return m[1]}}
function runtimeText(control){if(control?.resolvedText!==undefined&&control?.resolvedText!==null)return false;const p=control?.properties||{},raw=p.Text??p.Label??p.Title;if(raw===undefined)return true;if(exactLiteral(raw)!==null)return false;const text=String(raw);if(/^CEnvir\.Language\./.test(text))return false;return /GameScene|MapObject|Selected|Info\b|Item\b|User\b|Name\b|Count\b|Result\b|Value\b|Current|Partner|Guild|Quest|Dungeon|Fish|Horse|Milestone|Caption|\$"/.test(text)}
function install(root){
  if(!root?.id?.startsWith('w-')||root.dataset.sourceRuntimeBoundary==='true'||!spec)return;const id=root.id.slice(2),policy=POLICIES[id];if(!policy)return;const item=itemFor(root);if(!item)return;
  root.dataset.sourceRuntimeBoundary='true';root.dataset.sourceRuntimeData=policy.data;root.dataset.sourceRuntimeDataInvented='false';if(policy.server){root.dataset.sourceServerAction=policy.server;root.dataset.sourceServerActionExecuted='false'}
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=item.controls?.[index];if(!control)continue;
    if(control.type==='DXItemCell'||control.type==='DXItemGrid'){element.dataset.sourceItem='runtime-only';element.dataset.sourceItemInvented='false'}
    if(control.type==='DXLabel'&&runtimeText(control)){element.textContent='';element.dataset.sourceRuntimeText='true';element.dataset.sourceRuntimeTextInvented='false'}
    if(control.type==='DXImageControl'||control.type==='DXAnimatedControl'){
      const raw=String(control.properties?.Index??control.properties?.BaseIndex??'').trim();if(raw&&!/^-?\d+$/.test(raw)){element.dataset.sourceRuntimeImage='true';element.dataset.sourceRuntimeImageInvented='false'}
    }
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.id?.startsWith('w-'))queueMicrotask(()=>install(node));node.querySelectorAll?.('[id^="w-"]').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('[id^="w-"]').forEach(install);console.info(`ORIGINS runtime-bound source neutrality active for ${Object.keys(POLICIES).length} windows`) }).catch(error=>console.error('Unable to load runtime-bound window manifest',error));
