// Source-faithful visual behavior that is not part of geometry resolution.
// This file deliberately avoids fabricating player, item, map, chat or server data.
const stage=document.querySelector('#stage');
let sourceSpec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
const PRIMARY='rgb(198,166,99)';
const ACTIVE_TAB='#fff';
const INACTIVE_TAB='rgb(123,105,66)';

function boolFrom(raw,fallback=false){const value=String(raw??'').trim().toLowerCase();return value==='true'?true:value==='false'?false:fallback}
function intFrom(raw,fallback=null){const value=String(raw??'').trim();return /^-?\d+$/.test(value)?Number(value):fallback}
function floatFrom(raw,fallback=1){const value=String(raw??'').trim().replace(/[fFdDmM]$/,'');return /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(value)?Number(value):fallback}
function itemForRoot(root){
  if(!sourceSpec||!root?.id?.startsWith('w-'))return null;
  const id=root.id.slice(2);
  return [...(sourceSpec.windows||[]),...(sourceSpec.nestedWindows||[])].find(item=>item.id===id)||null;
}
function directQuoted(raw){return String(raw??'').match(/"([^"]*)"/)?.[1]??null}
function initializerText(raw){return String(raw??'').match(/\bText\s*=\s*"([^"]*)"/)?.[1]??null}
function deterministicText(control){
  if(typeof control?.resolvedText==='string')return control.resolvedText;
  const p=control?.properties||{};
  for(const raw of [p.TabButton,p.Label]){const text=initializerText(raw);if(text!==null)return text}
  for(const raw of [p.Text,p.Label]){const text=directQuoted(raw);if(text!==null)return text}
  return '';
}
function sourceColour(raw,fallback){
  const value=String(raw??'').trim();
  if(!value)return fallback;
  if(/Constants\.PrimaryColour/.test(value))return PRIMARY;
  if(/Constants\.ActiveTabColour/.test(value))return ACTIVE_TAB;
  if(/Constants\.InactiveTabColour/.test(value))return INACTIVE_TAB;
  if(/Color\.Empty\b/.test(value))return 'transparent';
  const named={Black:'#000',White:'#fff',Red:'#f00',Lime:'#0f0',Yellow:'#ff0',Cyan:'#0ff',Gray:'#808080',Grey:'#808080',Silver:'#c0c0c0',Gold:'#ffd700',Orange:'#ffa500'};
  const key=value.match(/Color\.([A-Za-z]+)/)?.[1];if(key&&named[key])return named[key];
  let match=value.match(/Color\.FromArgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);
  if(match)return `rgba(${match[2]},${match[3]},${match[4]},${Number(match[1])/255})`;
  match=value.match(/Color\.FromArgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);
  return match?`rgb(${match[1]},${match[2]},${match[3]})`:fallback;
}
function nestedProperty(raw,name){
  const match=String(raw??'').match(new RegExp(`\\b${name}\\s*=\\s*([^,}\\n]+)`));return match?.[1]?.trim()||null;
}

function installImageControl(element,control){
  if(!(element instanceof HTMLImageElement))return;
  const p=control.properties||{};
  const drawImage=boolFrom(p.DrawImage,true);
  element.style.display=drawImage?'':'none';
  if(!drawImage){element.dataset.sourceDrawImage='false';return}
  const imageOpacity=Math.max(0,Math.min(1,floatFrom(p.ImageOpacity,1)));
  element.style.opacity=String(imageOpacity);
  const disabled=!boolFrom(p.IsEnabled,true);
  const grayScale=boolFrom(p.GrayScale,false);
  const dropShadow=boolFrom(p.DropShadow,false);
  const filters=[];
  if(grayScale||disabled)filters.push('grayscale(1)');
  if(disabled)filters.push(`brightness(${75/255})`);
  if(dropShadow)filters.push('drop-shadow(0 0 8px rgba(0,0,0,.5))');
  element.style.filter=filters.join(' ');
  element.dataset.sourceImageOpacity=String(imageOpacity);
  element.dataset.sourceGrayScale=String(grayScale);
  element.dataset.sourceDropShadow=String(dropShadow);
  element.dataset.sourceBlend=String(boolFrom(p.Blend,false));
  element.dataset.sourceBlendMode=String(p.BlendMode??'BlendMode.NORMAL');
  element.dataset.sourceUseOffset=String(boolFrom(p.UseOffSet,false));
  element.dataset.sourceFixedSize=String(boolFrom(p.FixedSize,false));
  element.dataset.sourceIntersectParent=String(p.IntersectParent??'true');
}

function labelStyleFromInitializer(label,raw){
  const fore=nestedProperty(raw,'ForeColour');
  label.style.color=sourceColour(fore,PRIMARY);
  label.style.textShadow='1px 0 #000,0 1px #000,-1px 0 #000,0 -1px #000';
  label.style.fontSize='10.6667px';
  label.style.lineHeight='normal';
  label.style.pointerEvents='none';
}
function buttonType(control){return String(control.properties?.ButtonType??'ButtonType.Default').match(/ButtonType\.([A-Za-z0-9_]+)/)?.[1]||'Default'}
function ensureButtonLabel(element,control){
  if(!(element instanceof Element))return;
  const text=deterministicText(control);
  let label=element.querySelector(':scope > .dx-button-label,:scope > .source-button-label');
  const generated=element.classList.contains('dx-generated-button')||element.classList.contains('dx-tab-button');
  if(!label&&text&& !generated){
    label=document.createElement('div');label.className='source-button-label';
    label.style.position='absolute';label.style.left='0';label.style.right='0';label.style.textAlign='center';label.style.display='flex';label.style.alignItems='center';label.style.justifyContent='center';
    element.parentElement?.appendChild(label);
    const left=element.style.left||'0px',top=element.style.top||'0px',width=element.style.width||`${element.width||0}px`,height=element.style.height||`${element.height||0}px`;
    label.style.left=left;label.style.top=top;label.style.right='auto';label.style.width=width;label.style.height=height;
    label.dataset.buttonOverlayFor=control.name||'';
  }
  if(!label)return;
  label.textContent=text;
  labelStyleFromInitializer(label,control.properties?.Label);
  const type=buttonType(control);
  label.style.transform=(type==='SelectedTab'||type==='DeselectedTab')?'':'translateY(-1px)';
  if(/ButtonLabelStyle\.Gold/.test(String(control.properties?.LabelStyle??''))){
    label.style.background='linear-gradient(#fff4a6,#c5791a)';
    label.style.webkitBackgroundClip='text';label.style.backgroundClip='text';label.style.color='transparent';
  }
  element.dataset.sourceVisibleLabel=text?'deterministic':'none';
}
function installTab(element,control){
  if(!(element instanceof Element))return;
  ensureButtonLabel(element,control);
  const label=element.querySelector(':scope > .dx-button-label,:scope > .source-button-label');
  if(label){label.style.transform='';label.style.color=element.classList.contains('selected')?ACTIVE_TAB:INACTIVE_TAB}
  element.dataset.sourceTabMinimumWidth=String(intFrom(control.properties?.MinimumTabWidth,60));
}

function exactSliderBackground(scrollbar){
  scrollbar.querySelectorAll(':scope > .dx-scroll-bg,:scope > .source-slider-background').forEach(element=>element.remove());
  const size=sourceSpec?.assetSizes?.Interface?.['59'];
  if(!Array.isArray(size)||size.length!==2)return;
  const imageWidth=Number(size[0]),imageHeight=Number(size[1]);
  const width=Math.round(scrollbar.getBoundingClientRect().width||Number.parseFloat(scrollbar.style.width)||0);
  const height=Math.round(scrollbar.getBoundingClientRect().height||Number.parseFloat(scrollbar.style.height)||0);
  if(width<=0||height<=0||imageWidth<=0||imageHeight<=0)return;
  const root=document.createElement('div');root.className='source-slider-background';
  root.style.position='absolute';root.style.left='2px';root.style.top='0';root.style.width=`${width}px`;root.style.height=`${height}px`;root.style.overflow='hidden';root.style.pointerEvents='none';
  const addSlice=(top,sourceY,sliceHeight)=>{
    if(sliceHeight<=0)return;
    const clip=document.createElement('div');clip.style.position='absolute';clip.style.left='0';clip.style.top=`${top}px`;clip.style.width=`${width}px`;clip.style.height=`${sliceHeight}px`;clip.style.overflow='hidden';
    const image=document.createElement('img');image.src=asset('Interface',59);image.draggable=false;image.style.position='absolute';image.style.left='0';image.style.top=`${-sourceY}px`;image.style.width=`${width}px`;image.style.height=`${imageHeight}px`;image.style.pointerEvents='none';
    clip.append(image);root.append(clip);
  };
  const section=20;const topHeight=Math.min(section,height);addSlice(0,0,topHeight);
  let middleHeight=Math.max(0,height-topHeight-section),y=section;const middleSourceHeight=Math.max(0,imageHeight-section*2);
  while(middleHeight>0&&middleSourceHeight>0){const drawHeight=Math.min(middleSourceHeight,middleHeight);addSlice(y,section,drawHeight);y+=drawHeight;middleHeight-=drawHeight}
  const bottomHeight=Math.min(section,Math.max(0,height-topHeight));if(bottomHeight>0)addSlice(height-bottomHeight,Math.max(0,imageHeight-section),bottomHeight);
  scrollbar.prepend(root);scrollbar.dataset.sourceBackgroundSlider='Interface#59 sliced 20px top/middle/bottom';
}
function styleScrollBar(scrollbar,{tree=false,showBackground=false}={}){
  if(!(scrollbar instanceof Element))return;
  scrollbar.style.border=tree?'none':`1px solid ${PRIMARY}`;
  scrollbar.style.background=tree?'transparent':'#000';
  if(tree||showBackground)exactSliderBackground(scrollbar);
  else scrollbar.querySelectorAll(':scope > .dx-scroll-bg,:scope > .source-slider-background').forEach(element=>element.remove());
}
function installScrollBar(element,control){
  const p=control.properties||{};
  styleScrollBar(element,{showBackground:boolFrom(p.ShowBackgroundSlider,false),tree:false});
  element.dataset.sourceScrollBorder=String(boolFrom(p.Border,true));
}
function installInternalScrollbars(root){
  root.querySelectorAll('.dx-listbox > .dx-scrollbar').forEach(scrollbar=>styleScrollBar(scrollbar));
  root.querySelectorAll('.dx-tree-control > .dx-scrollbar').forEach(scrollbar=>styleScrollBar(scrollbar,{tree:true,showBackground:true}));
}

function removeTechnicalFallbacks(root,item){
  const heading=root.querySelector(':scope > .generic-window-header');
  if(heading&&heading.textContent.trim()===(item.field||'')){
    // DXWindow base text is only "Window" until a derived class supplies a real title.
    // Never replace missing source title text with a C# GameScene field name.
    heading.textContent='';heading.dataset.sourceTitleFallbackRemoved='true';
  }
  root.querySelectorAll('[title]').forEach(element=>{
    const title=element.getAttribute('title')||'';
    if(/:\s*DX(?:Button|ImageControl|AnimatedControl)$/.test(title)||/source preview:/i.test(title))element.removeAttribute('title');
  });
}
function installRoot(root){
  if(!sourceSpec||!(root instanceof Element)||!root.id?.startsWith('w-'))return;
  const item=itemForRoot(root);if(!item)return;
  const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;
    const control=controls[index];if(!control)continue;
    if(control.type==='DXImageControl'||control.type==='DXAnimatedControl')installImageControl(element instanceof HTMLImageElement?element:element.querySelector('img'),control);
    if(control.type==='DXButton')ensureButtonLabel(element,control);
    if(control.type==='DXTab'||control.type==='DXConfigTab')installTab(element,control);
    if(control.type==='DXVScrollBar'||control.type==='DXHScrollBar')installScrollBar(element,control);
  }
  installInternalScrollbars(root);removeTechnicalFallbacks(root,item);
}
function scan(node){
  if(!(node instanceof Element))return;
  if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>installRoot(node));
  node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>installRoot(root)));
}
new MutationObserver(records=>{
  for(const record of records){
    for(const node of record.addedNodes)scan(node);
    if(record.type==='attributes'&&record.target instanceof Element&&record.target.classList.contains('dx-tab-button')){
      const root=record.target.closest('.window,.generic-window');if(root)queueMicrotask(()=>installRoot(root));
    }
  }
}).observe(stage,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});

fetch('ui-source-spec.json',{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(spec=>{sourceSpec=spec;stage.querySelectorAll('.window,.generic-window').forEach(installRoot);console.info('ORIGINS visual control fidelity: image/button/tab/scrollbar source pass active')})
  .catch(error=>console.error('Unable to load visual control fidelity manifest',error));