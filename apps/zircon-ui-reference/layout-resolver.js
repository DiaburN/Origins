const NUM = /^-?\d+(?:\.\d+)?$/;

function boolValue(value, fallback=false) {
  const s=String(value??'').trim().toLowerCase();
  if(s==='true') return true;
  if(s==='false') return false;
  return fallback;
}
function numberValue(value, fallback=null) {
  const s=String(value??'').trim();
  return NUM.test(s)?Number(s):fallback;
}
function libraryFrom(expr) {
  const m=String(expr??'').match(/LibraryFile\.([A-Za-z0-9_]+)/);
  return m?m[1]:null;
}
function indexFrom(expr) {
  const m=String(expr??'').match(/\b(\d+)\b/);
  return m?Number(m[1]):null;
}
function textFrom(expr,fallback='') {
  if(!expr) return fallback;
  const quoted=String(expr).match(/"([^"]+)"/);
  if(quoted) return quoted[1];
  const lang=String(expr).match(/CEnvir\.Language\.([A-Za-z0-9_]+)/);
  return lang?lang[1].replace(/([a-z])([A-Z])/g,'$1 $2'):fallback;
}
function splitPairArgs(text) {
  let depth=0,inString=false,escaped=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(inString){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c==='"')inString=false;continue}
    if(c==='"'){inString=true;continue}
    if(c==='('||c==='['||c==='{')depth++;
    else if(c===')'||c===']'||c==='}')depth--;
    else if(c===','&&depth===0)return[text.slice(0,i),text.slice(i+1)];
  }
  return null;
}

export function getAssetSize(spec, library, index) {
  if(!library||index===null||index===undefined)return null;
  const raw=spec?.assetSizes?.[library]?.[String(index)];
  return Array.isArray(raw)&&raw.length===2?[Number(raw[0]),Number(raw[1])]:null;
}

function constantsFrom(spec) {
  const h=i=>getAssetSize(spec,'Interface',i)?.[1]||0;
  return {
    DefaultHeight:h(16)||20,
    TabHeight:h(19)||22,
    SmallButtonHeight:h(41)||18,
    ComboBoxDefaultNormalHeight:16,
    ItemCellWidth:36,
    ItemCellHeight:36,
    HeaderBarSize:h(0)||7,
    HeaderSize:(h(0)+h(3))||35,
    NoHeaderSize:h(2)||8,
    FooterSize:(h(126)+h(2)+h(10))||42,
    NoFooterSize:h(2)||8,
    SlimFooterSize:h(126)||20,
  };
}

function windowFlags(item) {
  const r=item.root||{};
  return {
    hasTop:boolValue(r.HasTopBorder,true),
    hasTitle:boolValue(r.HasTitle,true),
    hasFooter:boolValue(r.HasFooter,false),
    slimFooter:boolValue(r.SlimFooter,false),
  };
}
function isDxWindow(item) {
  const base=String(item.baseClass||'');
  return base.includes('DXWindow')||Boolean(item.root?.ClientSize);
}
function getWindowSize(client,flags,c) {
  const w=client[0]+18;
  let h=client[1]+12;
  if(!flags.hasTop)h+=c.NoHeaderSize;
  else if(flags.hasTitle)h+=c.HeaderSize;
  else h+=c.HeaderBarSize;
  h+=flags.hasFooter?c.FooterSize:c.NoFooterSize;
  return[w,h];
}
function getClientArea(size,flags,c) {
  const x=9;
  let y=6;
  if(!flags.hasTop)y+=c.NoHeaderSize;
  else if(flags.hasTitle)y+=c.HeaderSize;
  else y+=c.HeaderBarSize;
  const w=Math.max(0,size[0]-x*2);
  let h=size[1]-y-6;
  if(!flags.hasFooter){h+=c.NoFooterSize;if(flags.slimFooter)h-=c.SlimFooterSize}
  else h-=c.FooterSize;
  return{x,y,width:Math.max(0,w),height:Math.max(0,h),left:x,top:y,right:x+w,bottom:y+h};
}

function sanitiseMath(expr) {
  return expr.replace(/\((?:int|float|double|decimal)\)/g,'').replace(/\bf\b/gi,'');
}
function safeMath(expr) {
  const s=sanitiseMath(expr).trim();
  if(!/^[0-9+\-*/().\s]+$/.test(s))return null;
  try{
    // After the strict character whitelist this contains arithmetic only.
    const value=Function(`"use strict";return (${s})`)();
    return Number.isFinite(value)?value:null;
  }catch{return null}
}
function replaceMathFunctions(expr,env) {
  let s=expr;
  const fnRe=/Math\.(Min|Max|Round|Floor|Ceiling)\s*\(([^()]+)\)/g;
  for(let guard=0;guard<10;guard++){
    let changed=false;
    s=s.replace(fnRe,(all,fn,args)=>{
      const parts=splitPairArgs(args);
      let value=null;
      if(fn==='Min'||fn==='Max'){
        if(!parts)return all;
        const a=evaluateNumber(parts[0],env),b=evaluateNumber(parts[1],env);
        if(a===null||b===null)return all;
        value=fn==='Min'?Math.min(a,b):Math.max(a,b);
      }else{
        const v=evaluateNumber(args,env);if(v===null)return all;
        value=fn==='Round'?Math.round(v):fn==='Floor'?Math.floor(v):Math.ceil(v);
      }
      changed=true;return String(value);
    });
    if(!changed)break;
  }
  return s;
}
function geometryRef(env,name) {
  return env.byName.get(name)||null;
}
function replaceReferences(expr,env) {
  let s=expr;
  const root=env.root,client=env.client,c=env.constants;

  // Resolve named controls first. Root tokens such as `Size.Width` are also
  // suffixes of `CloseButton.Size.Width`; replacing the root token first would
  // corrupt the named expression before we get a chance to resolve it.
  s=s.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\.ValueTextBox\.Location\.(X|Y)\b/g,(all,name,dim)=>{
    const g=geometryRef(env,name);if(!g)return all;
    return String(dim==='X'?19:1);
  });
  s=s.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\.ValueTextBox\.Size\.(Width|Height)\b/g,(all,name,dim)=>{
    const g=geometryRef(env,name);if(!g)return all;
    return String(dim==='Width'?50:20);
  });
  s=s.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\.Size\.(Width|Height)\b/g,(all,name,dim)=>{
    const g=geometryRef(env,name);return g?String(dim==='Width'?g.width:g.height):all;
  });
  s=s.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\.Location\.(X|Y)\b/g,(all,name,dim)=>{
    const g=geometryRef(env,name);return g?String(dim==='X'?g.localX:g.localY):all;
  });
  s=s.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\.DisplayArea\.(X|Y|Left|Top|Right|Bottom|Width|Height)\b/g,(all,name,dim)=>{
    const g=geometryRef(env,name);if(!g)return all;
    const values={X:g.x,Y:g.y,Left:g.x,Top:g.y,Right:g.x+g.width,Bottom:g.y+g.height,Width:g.width,Height:g.height};
    return String(values[dim]);
  });

  const simple={
    'Size.Width':root.width,'Size.Height':root.height,
    'DisplayArea.Width':root.width,'DisplayArea.Height':root.height,
    'DisplayArea.X':0,'DisplayArea.Y':0,'DisplayArea.Left':0,'DisplayArea.Top':0,
    'DisplayArea.Right':root.width,'DisplayArea.Bottom':root.height,
    'ClientArea.X':client.x,'ClientArea.Y':client.y,'ClientArea.Left':client.left,'ClientArea.Top':client.top,
    'ClientArea.Right':client.right,'ClientArea.Bottom':client.bottom,'ClientArea.Width':client.width,'ClientArea.Height':client.height,
    'ClientArea.Location.X':client.x,'ClientArea.Location.Y':client.y,
    'DXComboBox.DefaultNormalHeight':c.ComboBoxDefaultNormalHeight,
    'DXItemCell.CellWidth':c.ItemCellWidth,'DXItemCell.CellHeight':c.ItemCellHeight,
    DefaultHeight:c.DefaultHeight,TabHeight:c.TabHeight,SmallButtonHeight:c.SmallButtonHeight,
  };
  for(const [key,val] of Object.entries(simple)){
    const escaped=key.replace(/\./g,'\\.');
    // Root Size/DisplayArea tokens must not match a suffix of NamedControl.Size.
    const prefix=(key.startsWith('Size.')||key.startsWith('DisplayArea.'))?'(?<!\\.)':'\\b';
    s=s.replace(new RegExp(`${prefix}${escaped}\\b`,'g'),String(val));
  }
  return s;
}
function evaluateNumber(expr,env) {
  if(expr===null||expr===undefined)return null;
  let s=String(expr).trim();
  const literal=numberValue(s,null);if(literal!==null)return literal;
  s=replaceReferences(s,env);
  s=replaceMathFunctions(s,env);
  return safeMath(s);
}
function evaluatePair(expr,type,env) {
  if(!expr)return null;
  const s=String(expr).trim();
  if((type==='Point'&&s==='Point.Empty')||(type==='Size'&&s==='Size.Empty'))return[0,0];
  if(type==='Point'&&s==='ClientArea.Location')return[env.client.x,env.client.y];
  if(type==='Size'&&s==='ClientArea.Size')return[env.client.width,env.client.height];
  const direct=s.match(new RegExp(`^([A-Za-z_][A-Za-z0-9_]*)\\.${type==='Point'?'Location':'Size'}$`));
  if(direct){const g=geometryRef(env,direct[1]);if(g)return type==='Point'?[g.localX,g.localY]:[g.width,g.height]}
  const m=s.match(new RegExp(`^new\\s+${type}\\s*\\((.*)\\)$`));
  if(!m)return null;
  const args=splitPairArgs(m[1]);if(!args)return null;
  const a=evaluateNumber(args[0],env),b=evaluateNumber(args[1],env);
  return a===null||b===null?null:[Math.round(a),Math.round(b)];
}

function rootSizeFor(spec,item,c) {
  const root=item.root||{},flags=windowFlags(item);
  const dummy={root:{width:1024,height:768},client:{x:0,y:0,left:0,top:0,right:1024,bottom:768,width:1024,height:768},constants:c,byName:new Map()};
  const explicit=evaluatePair(root.Size,'Size',dummy);
  if(explicit)return explicit;
  const client=evaluatePair(root.ClientSize,'Size',dummy);
  if(client)return isDxWindow(item)?getWindowSize(client,flags,c):client;
  const lib=libraryFrom(root.LibraryFile),idx=indexFrom(root.Index),art=getAssetSize(spec,lib,idx);
  if(art)return art;
  return item.category==='npc'?[420,300]:item.category==='hud'?[300,180]:[380,300];
}
function estimateTextSize(control,c) {
  const p=control.properties||{},text=textFrom(p.Text||p.Label||p.TabButton,control.name||'');
  const fontSize=Number(String(p.Font||'').match(/([0-9]+(?:\.[0-9]+)?)F?\b/)?.[1]||10);
  return[Math.max(8,Math.ceil(text.length*fontSize*.58)+(boolValue(p.Outline,false)?2:0)),Math.max(12,Math.ceil(fontSize+4))];
}
function defaultControlSize(spec,item,control,env,parent) {
  const p=control.properties||{};
  const exact=evaluatePair(p.Size,'Size',env);if(exact)return exact;
  const getSize=String(p.Size||'').match(/GetSize\s*\(\s*(\d+)\s*\)/);
  if(getSize){const lib=libraryFrom(p.LibraryFile)||libraryFrom(item.root?.LibraryFile)||'Interface';const s=getAssetSize(spec,lib,Number(getSize[1]));if(s)return s}
  const lib=libraryFrom(p.LibraryFile),idx=indexFrom(p.Index),art=getAssetSize(spec,lib,idx);if(art)return art;
  const grid=evaluatePair(p.GridSize,'Size',env);if(grid)return[grid[0]*36,grid[1]*36];
  const c=env.constants;
  switch(control.type){
    case'DXLabel':return estimateTextSize(control,c);
    case'DXButton':return[90,String(p.ButtonType||'').includes('SmallButton')?c.SmallButtonHeight:c.DefaultHeight];
    case'DXCheckBox':{const box=getAssetSize(spec,'GameInter',161)||[16,16],t=estimateTextSize(control,c);return[t[0]+box[0]+2,Math.max(t[1],box[1])];}
    case'DXItemCell':return[36,36];
    case'DXItemGrid':return[145,145];
    case'DXVScrollBar':return[16,120];
    case'DXHScrollBar':return[120,16];
    case'DXTextBox':case'DXNumberTextBox':return[120,20];
    case'DXNumberBox':return[90,c.DefaultHeight];
    case'DXComboBox':return[120,16];
    case'DXColourControl':return[40,15];
    case'DXListBox':return[160,120];
    case'DXSoundBar':return[180,18];
    case'DXTreeControl':return[220,210];
    case'DXTabControl':return[parent?.width||env.root.width,parent?.height||env.root.height];
    case'DXTab':case'DXConfigTab':return[parent? [parent.width,Math.max(0,parent.height-c.TabHeight+1)]:[env.root.width,env.root.height-c.TabHeight+1]];
    default:return[80,28];
  }
}
function parentName(control) {
  const raw=String(control.properties?.Parent??'this').trim();
  return /^[A-Za-z_][A-Za-z0-9_]*$/.test(raw)&&raw!=='this'?raw:null;
}

export function buildWindowLayout(spec,item) {
  const constants=constantsFrom(spec),flags=windowFlags(item),rootSize=rootSizeFor(spec,item,constants);
  const client=isDxWindow(item)?getClientArea(rootSize,flags,constants):{x:0,y:0,left:0,top:0,right:rootSize[0],bottom:rootSize[1],width:rootSize[0],height:rootSize[1]};
  const root={x:0,y:0,localX:0,localY:0,width:rootSize[0],height:rootSize[1],parent:null,visible:true};
  const env={root,client,constants,byName:new Map()};
  const nodes=[];
  const tabState=new Map();

  for(let i=0;i<(item.controls||[]).length;i++){
    const control=item.controls[i],p=control.properties||{},pname=parentName(control),parent=pname?env.byName.get(pname):root,parentGeom=parent||root;
    const provisional={x:parentGeom.x,y:parentGeom.y,localX:0,localY:0,width:0,height:0,parent:parentGeom,visible:parentGeom.visible!==false};
    env.byName.set(control.name,provisional);
    let size=defaultControlSize(spec,item,control,env,parentGeom);
    provisional.width=size[0];provisional.height=size[1];
    let local=evaluatePair(p.Location,'Point',env);
    if(!local&&(control.type==='DXTab'||control.type==='DXConfigTab'))local=[0,constants.TabHeight-1];
    if(!local)local=[0,0];
    provisional.localX=local[0];provisional.localY=local[1];provisional.x=parentGeom.x+local[0];provisional.y=parentGeom.y+local[1];
    if((control.type==='DXTab'||control.type==='DXConfigTab')&&!p.Size){
      provisional.width=Math.max(0,parentGeom.width-local[0]);provisional.height=Math.max(0,parentGeom.height-local[1]);
    }
    provisional.visible=provisional.visible&&p.Visible!=='false';
    provisional.name=control.name;provisional.type=control.type;provisional.control=control;provisional.index=i;provisional.parentName=pname;

    if(control.type==='DXTab'||control.type==='DXConfigTab'){
      const key=pname||'__root_tabs__';
      const state=tabState.get(key)||{x:0,count:0};
      const minWidth=evaluateNumber(p.MinimumTabWidth,env)||60;
      const textSize=estimateTextSize(control,constants);
      const bw=Math.max(minWidth,textSize[0]+8),selected=state.count===0;
      provisional.tabButton={x:parentGeom.x+state.x,y:parentGeom.y,width:bw,height:constants.TabHeight,selected};
      provisional.visible=provisional.visible&&selected;
      state.x+=bw+1;state.count++;tabState.set(key,state);
    }

    env.byName.set(control.name,provisional);
    nodes.push(provisional);
  }

  // A child of a hidden tab/container is hidden too. Re-run after all parent links exist.
  for(const node of nodes){
    let parent=node.parent,visible=node.visible;
    while(parent&&parent!==root){visible=visible&&parent.visible!==false;parent=parent.parent}
    node.visible=visible;
  }
  return{rootSize,clientArea:client,constants,nodes,byName:env.byName};
}

export function resolveRootAsset(spec,item) {
  const lib=libraryFrom(item.root?.LibraryFile),index=indexFrom(item.root?.Index);
  return{library:lib,index,size:getAssetSize(spec,lib,idx)};
}
