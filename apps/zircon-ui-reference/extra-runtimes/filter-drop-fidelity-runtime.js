// Source-faithful FilterDropDialog local editing. Ten checked-in empty filters are
// editable; Save updates only the local Config.HighlightedItems reference state.
const stage=document.querySelector('#stage');
const COUNT=10;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function generatedBox(root,index){return control(root,`FilterDropGeneratedTextBox${String(index+1).padStart(2,'0')}`)}
function textValue(box){return String(box?.textContent??'')}
function install(root){
  if(!root||root.id!=='w-filter-drop'||root.dataset.sourceFilterDropRuntime==='true')return;
  root.dataset.sourceFilterDropRuntime='true';root.dataset.sourceFilterCount=String(COUNT);root.dataset.configHighlightedItems='';root.dataset.sourceHighlightedItems='checked-in Config.HighlightedItems default string.Empty';root.dataset.sourceFilterRuntimeConfigInvented='false';
  for(let i=0;i<COUNT;i++){
    const box=generatedBox(root,i);if(!box)continue;box.contentEditable='true';box.spellcheck=false;box.setAttribute('role','textbox');box.dataset.sourceMaxLength='100';box.dataset.sourceFilterIndex=String(i);box.textContent='';
  }
  let save=control(root,'filterButton')||control(root,'FilterButton')||control(root,'SaveButton');
  if(!save)save=[...root.querySelectorAll('[data-control-type="DXButton"]')].find(button=>/save/i.test(button.textContent||''))||null;
  if(save&&save.dataset.sourceFilterSaveBound!=='true'){
    save.dataset.sourceFilterSaveBound='true';save.addEventListener('click',event=>{
      event.preventDefault();event.stopImmediatePropagation();const values=Array.from({length:COUNT},(_,i)=>textValue(generatedBox(root,i)));
      root.dataset.configHighlightedItems=values.join(',');root.dataset.sourceFilterSaveAction='Config.HighlightedItems = string.Join(",", TextBoxes.Select(...))';root.dataset.sourceFilterSaveChat='CEnvir.Language.FilterDialogSaveMessage (game chat not fabricated)';root.dataset.sourceFilterSaveChatExecuted='false';
    },true);
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-filter-drop')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-filter-drop').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-filter-drop'));
console.info('ORIGINS FilterDrop source runtime active: 10 editable filters + local Config.HighlightedItems save');
