import { buildWindowLayout } from './layout-resolver-derived.js';

const stage = document.querySelector('#stage');
let zCounter = 100;
let sourceSpec = null;
const pad=value=>String(value).padStart(5,'0');
const sourceAsset=(library,index)=>`assets/${library}/${pad(index)}.png`;

function isWindow(element) {
  return element instanceof HTMLElement && (element.classList.contains('window') || element.classList.contains('generic-window'));
}
function boolFrom(raw,fallback=false) {
  const value=String(raw??'').trim().toLowerCase();
  if(value==='true')return true;if(value==='false')return false;return fallback;
}
function sourceFloat(raw,fallback=1) {
  const value=String(raw??'').trim().replace(/[fFdDmM]$/,'');
  return /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(value)?Number(value):fallback;
}
function sourceInt(raw,fallback=null) {
  const value=String(raw??'').trim();
  return /^-?\d+$/.test(value)?Number(value):fallback;
}
function sourceLibrary(raw) {
  return String(raw??'').match(/LibraryFile\.([A-Za-z0-9_]+)/)?.[1]||null;
}
function sourceIndex(raw) {
  const value=String(raw??'').trim();
  return /^-?\d+$/.test(value)?Number(value):null;
}

function focusWindow(root) {
  if (!isWindow(root)) return;
  zCounter += 1;
  root.style.zIndex = String(zCounter);
  document.querySelectorAll('.window.focused,.generic-window.focused').forEach(element => {
    if (element !== root) element.classList.remove('focused');
  });
  root.classList.add('focused');
}

function storageKey(root) { return root.id ? `origins-zircon-window:${root.id}` : null; }
function restorePosition(root) {
  const key = storageKey(root); if (!key) return;
  try {
    const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (!saved || !Number.isFinite(saved.x) || !Number.isFinite(saved.y)) return;
    root.style.left = `${saved.x}px`; root.style.top = `${saved.y}px`;
  } catch {}
}
function savePosition(root) {
  const key=storageKey(root);if(!key)return;
  const x=Number.parseFloat(root.style.left||'0'),y=Number.parseFloat(root.style.top||'0');
  if(Number.isFinite(x)&&Number.isFinite(y))sessionStorage.setItem(key,JSON.stringify({x,y}));
}
function clearCatalogState(root) {
  if (!isWindow(root) || !root.id?.startsWith('w-')) return;
  const id = root.id.slice(2);
  document.querySelector(`[data-window-id="${CSS.escape(id)}"]`)?.classList.remove('active');
}
function isInteractiveTarget(target) {
  return target instanceof Element && Boolean(target.closest('button,input,textarea,select,.close,.ui-button,.dx-generated-button,.dx-checkbox,.dx-scrollbar,.dx-textbox'));
}
function sourceItemForRoot(root) {
  if (!sourceSpec || !root?.id?.startsWith('w-')) return null;
  const id=root.id.slice(2);
  return [...(sourceSpec.windows||[]),...(sourceSpec.nestedWindows||[])].find(item=>item.id===id)||null;
}

function intersect(a,b) {
  const left=Math.max(a.left,b.left),top=Math.max(a.top,b.top),right=Math.min(a.right,b.right),bottom=Math.min(a.bottom,b.bottom);
  return {left,top,right,bottom,width:Math.max(0,right-left),height:Math.max(0,bottom-top)};
}
function sourceClipArea(node) {
  let clip={left:node.x,top:node.y,right:node.x+node.width,bottom:node.y+node.height,width:node.width,height:node.height};
  let parent=node.parent;
  while(parent) {
    clip=intersect(clip,{left:parent.x,top:parent.y,right:parent.x+parent.width,bottom:parent.y+parent.height,width:parent.width,height:parent.height});
    parent=parent.parent;
  }
  return clip;
}
function numericStyle(element,key,fallback) {
  const value=Number.parseFloat(element.style[key]||'');return Number.isFinite(value)?value:fallback;
}
function applyClipToElement(element,node,clip) {
  if (!(element instanceof HTMLElement) && !(element instanceof SVGElement)) return;
  const apply=()=>{
    const x=numericStyle(element,'left',node.x),y=numericStyle(element,'top',node.y);
    const width=numericStyle(element,'width',element.offsetWidth||node.width),height=numericStyle(element,'height',element.offsetHeight||node.height);
    const box={left:x,top:y,right:x+width,bottom:y+height,width,height},visible=intersect(box,clip);
    element.dataset.sourceClipArea=`${clip.left},${clip.top},${clip.right},${clip.bottom}`;
    if(visible.width<=0||visible.height<=0) {element.style.visibility='hidden';element.dataset.sourceFullyClipped='true';return}
    element.style.visibility='';element.dataset.sourceFullyClipped='false';
    const top=Math.max(0,visible.top-box.top),right=Math.max(0,box.right-visible.right),bottom=Math.max(0,box.bottom-visible.bottom),left=Math.max(0,visible.left-box.left);
    if(top||right||bottom||left){element.style.clipPath=`inset(${top}px ${right}px ${bottom}px ${left}px)`;element.dataset.sourceClipApplied='true'}
    else{element.style.clipPath='';element.dataset.sourceClipApplied='false'}
  };
  apply();if(element instanceof HTMLImageElement&&!element.complete)element.addEventListener('load',apply,{once:true});
}

function indexedButtonImage(element) {
  if(element instanceof HTMLImageElement)return element;
  return element.querySelector?.('img.nested-source-indexed-art,img.nested-source-indexed-image,img.nested-indexed-image')||null;
}
function installIndexedButtonStates(element,node,enabled) {
  if(node.control?.type!=='DXButton'||!enabled||element.dataset.sourceButtonStateInstalled==='true')return false;
  const p=node.control?.properties||{},library=sourceLibrary(p.LibraryFile),normal=sourceIndex(p.Index),hover=sourceIndex(p.HoverIndex),pressed=sourceIndex(p.PressedIndex);
  if(!library||normal===null||normal<0)return false;
  const hasHover=hover!==null&&hover>=0,hasPressed=pressed!==null&&pressed>=0;
  if(!hasHover&&!hasPressed)return false;
  const image=indexedButtonImage(element);
  if(!image)return false;
  const states={normal,hover:hasHover?hover:normal,pressed:hasPressed?pressed:(hasHover?hover:normal)};
  const setState=state=>{
    const index=states[state];image.src=sourceAsset(library,index);
    element.dataset.sourceButtonState=state;element.dataset.sourceButtonStateIndex=String(index);
  };
  element.style.pointerEvents='auto';element.style.cursor='pointer';
  element.dataset.sourceButtonStateInstalled='true';
  element.dataset.sourceButtonStateAssets=`${library}:${states.normal}/${states.hover}/${states.pressed}`;
  setState('normal');
  element.addEventListener('pointerenter',()=>setState('hover'));
  element.addEventListener('pointerleave',()=>setState('normal'));
  element.addEventListener('pointerdown',event=>{if(event.button===0)setState('pressed')});
  element.addEventListener('pointerup',()=>setState(element.matches(':hover')?'hover':'normal'));
  element.addEventListener('pointercancel',()=>setState('normal'));
  return true;
}

function installTextBoxBehavior(element,node,enabled) {
  const type=node.control?.type;
  if(type!=='DXTextBox'&&type!=='DXNumberTextBox')return false;
  if(element.dataset.sourceTextBoxInstalled==='true')return true;
  const p=node.control?.properties||{};
  const editable=enabled&&boolFrom(p.Editable,true)&&!boolFrom(p.ReadOnly,false);
  const readOnly=boolFrom(p.ReadOnly,false);
  const password=boolFrom(p.Password,false);
  const maxLength=sourceInt(p.MaxLength,0);

  element.dataset.sourceTextBoxInstalled='true';
  element.dataset.sourceEditable=String(editable);
  element.dataset.sourceReadOnly=String(readOnly);
  element.dataset.sourcePassword=String(password);
  if(maxLength>0)element.dataset.sourceMaxLength=String(maxLength);
  element.setAttribute('role','textbox');
  element.setAttribute('aria-readonly',String(!editable));
  element.contentEditable=editable?'true':'false';
  element.tabIndex=editable?0:-1;
  element.style.cursor=editable?'text':'default';
  element.style.userSelect=editable?'text':'none';
  if(password) {
    element.style.webkitTextSecurity='disc';
    element.dataset.sourcePasswordMask='system-password-char';
  }
  if(type==='DXNumberTextBox') {
    element.setAttribute('inputmode','numeric');
    element.dataset.sourceNumeric='true';
  }

  if(editable) {
    element.addEventListener('focus',()=>{element.dataset.sourceActiveTextBox='true'});
    element.addEventListener('blur',()=>{element.dataset.sourceActiveTextBox='false'});
    element.addEventListener('input',()=>{
      if(type==='DXNumberTextBox') {
        const caretSelection=window.getSelection();
        const cleaned=(element.textContent||'').replace(/[^0-9-]/g,'');
        if(cleaned!==element.textContent)element.textContent=cleaned;
        caretSelection?.collapse?.(element,element.childNodes.length);
      }
      if(maxLength>0&&(element.textContent||'').length>maxLength) {
        element.textContent=(element.textContent||'').slice(0,maxLength);
        const selection=window.getSelection();selection?.collapse?.(element,element.childNodes.length);
      }
      element.dataset.runtimeValue=element.textContent||'';
    });
  }
  return true;
}

function resolvedScrollProperty(properties,name,defaultValue) {
  if(properties[name]===undefined)return {resolved:true,value:defaultValue,source:'default'};
  const value=sourceInt(properties[name],null);
  return {resolved:value!==null,value,source:String(properties[name])};
}
function setInternalScrollButtonState(image,enabled) {
  if(!image)return;
  image.dataset.sourceEnabled=String(enabled);
  image.style.pointerEvents=enabled?'auto':'none';
  image.style.cursor=enabled?'pointer':'default';
  image.style.filter=enabled?'':`brightness(${51/217})`;
}
function installScrollBarBehavior(element,node,enabled) {
  const type=node.control?.type;
  if(type!=='DXVScrollBar'&&type!=='DXHScrollBar')return false;
  if(element.dataset.sourceScrollInstalled==='true')return true;
  const p=node.control?.properties||{};
  const vertical=type==='DXVScrollBar';
  const minProp=resolvedScrollProperty(p,'MinValue',0);
  const maxProp=resolvedScrollProperty(p,'MaxValue',0);
  const visibleProp=resolvedScrollProperty(p,'VisibleSize',0);
  const valueProp=resolvedScrollProperty(p,'Value',0);
  const changeProp=resolvedScrollProperty(p,'Change',10);
  const deterministic=[minProp,maxProp,visibleProp,valueProp,changeProp].every(item=>item.resolved);

  element.dataset.sourceScrollInstalled='true';
  element.dataset.sourceScrollAxis=vertical?'vertical':'horizontal';
  element.dataset.sourceScrollDeterministic=String(deterministic);
  element.dataset.sourceHideWhenNoScroll=String(boolFrom(p.HideWhenNoScroll,false));

  const background=element.querySelector('img.dx-scroll-bg');
  const thumb=element.querySelector('img.dx-scroll-thumb');
  const buttons=[...element.querySelectorAll('img')].filter(image=>image!==background&&image!==thumb);
  const previous=buttons[0]||null,next=buttons[1]||null;
  if(!deterministic||!enabled) {
    setInternalScrollButtonState(previous,false);setInternalScrollButtonState(next,false);setInternalScrollButtonState(thumb,false);
    element.dataset.sourceScrollRuntimeContract=deterministic?'parent control disabled':'Value/MinValue/MaxValue/VisibleSize/Change require runtime expression';
    return true;
  }

  const min=minProp.value,max=maxProp.value,visible=Math.max(0,visibleProp.value),change=Math.max(0,changeProp.value);
  const maxScroll=Math.max(0,max-min-visible);
  const scrollExtent=Math.max(0,(vertical?node.height:node.width)-50);
  let value=Math.max(min,Math.min(max-visible,valueProp.value));
  const hideWhenNoScroll=boolFrom(p.HideWhenNoScroll,false);

  const update=()=>{
    value=Math.max(min,Math.min(max-visible,value));
    const canPrevious=value>min,canNext=value<max-visible,canMove=max-min>visible;
    setInternalScrollButtonState(previous,canPrevious);
    setInternalScrollButtonState(next,canNext);
    setInternalScrollButtonState(thumb,canMove);
    if(thumb&&maxScroll>0) {
      const position=16+Math.trunc(scrollExtent*((value-min)/maxScroll));
      if(vertical)thumb.style.top=`${position}px`;else thumb.style.left=`${position}px`;
    }
    element.dataset.value=String(value);
    element.dataset.sourceScrollRange=`${min}:${max}:${visible}:${change}`;
    if(hideWhenNoScroll)element.style.display=(canPrevious||canNext)?'':'none';
  };
  const setValue=nextValue=>{value=Math.max(min,Math.min(max-visible,Math.round(nextValue)));update()};
  update();

  previous?.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setValue(value-change)});
  next?.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setValue(value+change)});
  element.addEventListener('wheel',event=>{
    event.preventDefault();event.stopPropagation();
    const steps=event.deltaY===0?0:(event.deltaY>0?1:-1);
    setValue(value+steps*change);
  },{passive:false});
  element.addEventListener('pointerdown',event=>{
    if(event.button!==0||event.target===previous||event.target===next||event.target===thumb||maxScroll<=0)return;
    const rect=element.getBoundingClientRect();
    const pointer=vertical?event.clientY-rect.top:event.clientX-rect.left;
    const thumbSize=vertical?(thumb?.offsetHeight||13):(thumb?.offsetWidth||13);
    const nextValue=Math.round((pointer-(thumbSize+thumbSize/2))*maxScroll/Math.max(1,scrollExtent))+min;
    setValue(nextValue);
  });
  if(thumb)thumb.addEventListener('pointerdown',event=>{
    if(event.button!==0||maxScroll<=0)return;
    event.preventDefault();event.stopPropagation();
    thumb.setPointerCapture?.(event.pointerId);
    const rect=element.getBoundingClientRect();
    const thumbRect=thumb.getBoundingClientRect();
    const grabOffset=vertical?event.clientY-thumbRect.top:event.clientX-thumbRect.left;
    const move=moveEvent=>{
      const pointer=vertical?moveEvent.clientY-rect.top:moveEvent.clientX-rect.left;
      const thumbSize=vertical?(thumb.offsetHeight||13):(thumb.offsetWidth||13);
      const position=Math.max(16,Math.min(16+scrollExtent,pointer-grabOffset));
      setValue(Math.round((position-16)*maxScroll/Math.max(1,scrollExtent))+min);
    };
    const end=endEvent=>{
      thumb.releasePointerCapture?.(endEvent.pointerId);
      thumb.removeEventListener('pointermove',move);thumb.removeEventListener('pointerup',end);thumb.removeEventListener('pointercancel',end);
    };
    thumb.addEventListener('pointermove',move);thumb.addEventListener('pointerup',end);thumb.addEventListener('pointercancel',end);
  });
  return true;
}

function applySourceVisualState(element,node) {
  const p=node.control?.properties||{};
  if(p.Opacity!==undefined) {
    const opacity=Math.max(0,Math.min(1,sourceFloat(p.Opacity,1)));
    element.style.opacity=String(opacity);element.dataset.sourceOpacity=String(opacity);
  }
  const enabled=p.Enabled===undefined?true:boolFrom(p.Enabled,true);
  if(p.Enabled!==undefined) element.dataset.sourceEnabled=String(enabled);
  if(!enabled) {
    element.style.pointerEvents='none';
    if(node.control?.type==='DXButton') {
      const brightness=51/217;
      element.style.filter=`brightness(${brightness})`;
      element.dataset.sourceDisabledButtonTint='51/217';
    }
  }
  const textBox=installTextBoxBehavior(element,node,enabled);
  const scrollBar=installScrollBarBehavior(element,node,enabled);
  return {enabled,textBox,scrollBar,statefulIndexedButton:installIndexedButtonStates(element,node,enabled)};
}

function applySourceControlTree(root) {
  const item=sourceItemForRoot(root);if(!item||!sourceSpec)return;
  const layout=buildWindowLayout(sourceSpec,item);let applied=0,opacityCount=0,disabledCount=0,statefulButtonCount=0,textBoxCount=0,scrollBarCount=0;
  for(let i=0;i<layout.nodes.length;i++) {
    const node=layout.nodes[i],element=root.querySelector(`[data-control-index="${i}"]`);if(!element)continue;
    applyClipToElement(element,node,sourceClipArea(node));
    const visual=applySourceVisualState(element,node);
    if(node.control?.properties?.Opacity!==undefined)opacityCount++;
    if(node.control?.properties?.Enabled!==undefined&&!visual.enabled)disabledCount++;
    if(visual.statefulIndexedButton)statefulButtonCount++;
    if(visual.textBox)textBoxCount++;
    if(visual.scrollBar)scrollBarCount++;
    applied++;
  }
  root.dataset.sourceClipNodes=String(applied);
  root.dataset.sourceClipPolicy='DXControl.UpdateClipArea';
  root.dataset.sourceOpacityNodes=String(opacityCount);
  root.dataset.sourceDisabledNodes=String(disabledCount);
  root.dataset.sourceIndexedButtonStateNodes=String(statefulButtonCount);
  root.dataset.sourceTextBoxNodes=String(textBoxCount);
  root.dataset.sourceScrollBarNodes=String(scrollBarCount);
  root.dataset.sourceVisualStatePolicy='DXControl ClipArea/Opacity/Enabled + DXButton indexed states + DXTextBox semantics + DXV/HScrollBar Value/Min/Max/VisibleSize/Change';
}

function installDrag(root) {
  if (!isWindow(root) || root.dataset.originsDesktopRuntime === '1') return;
  root.dataset.originsDesktopRuntime = '1';restorePosition(root);focusWindow(root);queueMicrotask(()=>applySourceControlTree(root));
  root.addEventListener('origins:focus', () => focusWindow(root));
  root.addEventListener('pointerdown', event => {
    focusWindow(root);if(event.button!==0||isInteractiveTarget(event.target))return;
    const rect=root.getBoundingClientRect(),localY=event.clientY-rect.top;
    const explicitHandle=event.target instanceof Element&&Boolean(event.target.closest('.window-title,.generic-window-header'));
    if(!explicitHandle&&localY>34)return;
    event.preventDefault();root.setPointerCapture?.(event.pointerId);
    const stageRect=stage.getBoundingClientRect(),startX=event.clientX,startY=event.clientY,startLeft=Number.parseFloat(root.style.left||'0'),startTop=Number.parseFloat(root.style.top||'0');
    const move=moveEvent=>{
      const width=root.offsetWidth,height=root.offsetHeight,rawX=startLeft+(moveEvent.clientX-startX),rawY=startTop+(moveEvent.clientY-startY);
      const maxX=Math.max(0,stageRect.width-Math.min(width,stageRect.width)),maxY=Math.max(0,stageRect.height-Math.min(34,height));
      root.style.left=`${Math.round(Math.max(0,Math.min(maxX,rawX)))}px`;root.style.top=`${Math.round(Math.max(0,Math.min(maxY,rawY)))}px`;
    };
    const end=endEvent=>{root.releasePointerCapture?.(endEvent.pointerId);root.removeEventListener('pointermove',move);root.removeEventListener('pointerup',end);root.removeEventListener('pointercancel',end);savePosition(root)};
    root.addEventListener('pointermove',move);root.addEventListener('pointerup',end);root.addEventListener('pointercancel',end);
  });
}
function scan(node){if(!(node instanceof Element))return;if(isWindow(node))installDrag(node);node.querySelectorAll?.('.window,.generic-window').forEach(installDrag)}
function scanRemoved(node){if(!(node instanceof Element))return;if(isWindow(node))clearCatalogState(node);node.querySelectorAll?.('.window,.generic-window').forEach(clearCatalogState)}
new MutationObserver(records=>{for(const record of records){record.addedNodes.forEach(scan);record.removedNodes.forEach(scanRemoved)}}).observe(stage,{childList:true,subtree:true});

fetch('ui-source-spec.json',{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(spec=>{
    sourceSpec=spec;
    stage.querySelectorAll('.window,.generic-window').forEach(root=>{installDrag(root);applySourceControlTree(root)});
    console.info('ORIGINS source ClipArea/Opacity/Enabled/indexed-button/textbox/scrollbar runtime active');
  })
  .catch(error=>console.error('Unable to load Zircon source visual-state manifest',error));

stage.querySelectorAll('.window,.generic-window').forEach(installDrag);
document.querySelector('#reset-layout')?.addEventListener('click',()=>{for(const key of Object.keys(sessionStorage)){if(key.startsWith('origins-zircon-window:'))sessionStorage.removeItem(key)}});
