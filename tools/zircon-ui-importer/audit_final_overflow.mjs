import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const buildRoot=path.resolve(process.argv[2]||'.build/zircon-ui');
const spec=JSON.parse(fs.readFileSync(path.join(buildRoot,'ui-source-spec.json'),'utf8'));
const {buildWindowLayout}=await import(pathToFileURL(path.join(buildRoot,'layout-resolver-derived.js')).href);

const explained=[];
const unexpected=[];
const checked=[];

function simpleParent(control){
  const raw=String(control?.properties?.Parent??'this').trim();
  return raw===''||raw==='this'||raw==='ActiveScene'?null:raw;
}
function outside(node,width,height,rootSize){
  const [rw,rh]=rootSize;
  return node.x<0||node.y<0||node.x+width>rw||node.y+height>rh;
}
function describe(window,control,node,width,height,rootSize){
  return {
    window:window.field||window.sourceClass||window.class||window.id,
    id:window.id||null,
    control:control.name,
    type:control.type,
    root:rootSize,
    rect:[node.x,node.y,width,height],
    contract:control.overflowContract||null,
  };
}

for(const window of [...(spec.windows||[]),...(spec.nestedWindows||[])]){
  const layout=buildWindowLayout(spec,window);
  const rootSize=layout.rootSize||[layout.root?.width||0,layout.root?.height||0];
  for(let i=0;i<(window.controls||[]).length;i++){
    const control=window.controls[i],node=layout.nodes?.[i];
    if(!node||!node.visible||control.sourceNeutralVisible===false)continue;
    if(control.type==='DXTabControl')continue;
    // Child controls are governed by parent clipping/auto-layout. This audit is
    // specifically for controls whose source parent is the window/scene root.
    if(simpleParent(control))continue;
    const width=Number(control.sourceResolvedWidth??node.width);
    const height=Number(control.sourceResolvedHeight??node.height);
    if(!Number.isFinite(width)||!Number.isFinite(height))continue;
    checked.push([window.id||window.field,control.name]);
    if(!outside(node,width,height,rootSize))continue;
    const row=describe(window,control,node,width,height,rootSize);
    if(control.overflowContract)explained.push(row);else unexpected.push(row);
  }
}

console.log('Top-level visible controls checked for overflow:',checked.length);
console.log('Source-explained overflow contracts hit:',explained.length);
for(const row of explained)console.log('EXPLAINED',JSON.stringify(row));
console.log('Unexplained overflows:',unexpected.length);
for(const row of unexpected)console.log('UNEXPLAINED',JSON.stringify(row));

const pass=spec.overflowContractPass||{};
if(pass.contractCount!==5)throw new Error(`overflow contract inventory changed: ${JSON.stringify(pass)}`);
if(unexpected.length)throw new Error(`unexplained source-window overflow: ${unexpected.length}`);

// Some contracts are source/runtime conditional and may be neutral-hidden in
// this exact artifact, so not every declared contract must physically overflow.
// But the high-risk constructor cases should remain represented in the manifest.
const kinds=new Set();
for(const window of [...(spec.windows||[]),...(spec.nestedWindows||[])])
  for(const control of window.controls||[])
    if(control.overflowContract?.kind)kinds.add(control.overflowContract.kind);
for(const required of ['SOURCE_RUNTIME_RELOCATION','RUNTIME_SIZED_MINIGAME','SOURCE_OFFSET_PARENT_CLIP','SOURCE_BEFORE_DRAW_HIDDEN','PARTIAL_DYNAMIC_SIZE'])
  if(!kinds.has(required))throw new Error(`missing overflow contract kind: ${required}`);

console.log('Zero-unexplained-overflow contract: PASS');
