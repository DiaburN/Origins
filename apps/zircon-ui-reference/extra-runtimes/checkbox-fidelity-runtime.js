// Source-faithful DXCheckBox state on top of the base renderer. Zircon toggles
// only when the control is enabled and ReadOnly=false; Box follows measured
// label width plus LabelBoxPadding and uses GameInter 161/162.
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function boolFrom(raw,fallback=false){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function intFrom(raw,fallback=0){const v=String(raw??'').trim();return /^-?\d+$/.test(v)?Number(v):fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function apply(root){
  const item=itemFor(root);if(!item)return;const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index][data-control-type="DXCheckBox"]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=controls[index];if(!control)continue;
    const p=control.properties||{},readOnly=boolFrom(p.ReadOnly,false),enabled=boolFrom(p.IsEnabled,true),padding=intFrom(p.LabelBoxPadding,0),checked=boolFrom(p.Checked,false);
    const label=element.querySelector(':scope > span'),box=element.querySelector(':scope > img');
    if(box){box.src=asset('GameInter',checked?162:161);box.style.marginLeft=`${padding}px`;box.style.marginTop='1px';box.style.filter=enabled?'':`brightness(${51/217})`}
    element.dataset.sourceReadOnly=String(readOnly);element.dataset.sourceEnabled=String(enabled);element.dataset.sourceLabelBoxPadding=String(padding);element.dataset.sourceChecked=String(checked);
    if(label)label.style.pointerEvents='none';
    if(element.dataset.sourceCheckboxGuard!=='true'){
      element.dataset.sourceCheckboxGuard='true';
      element.addEventListener('click',event=>{
        const currentItem=itemFor(root);const currentControl=currentItem?.controls?.[index];const props=currentControl?.properties||p;
        const ro=boolFrom(element.dataset.sourceReadOnly??props.ReadOnly,false),en=boolFrom(element.dataset.sourceEnabled??props.IsEnabled,true);
        if(en&&!ro)return; // allow the original source-style toggle handler
        event.preventDefault();event.stopImmediatePropagation();
      },true);
    }
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(apply);console.info('ORIGINS Zircon DXCheckBox readonly/enabled/padding fidelity active')}).catch(error=>console.error('Unable to load checkbox fidelity manifest',error));