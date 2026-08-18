// Source-faithful DXConfigWindow standalone state. In the real client the window
// reads current Zircon.ini values in OnVisibleChanged. The reference viewer has no
// user machine config, so the manifest supplies Config.cs checked-in defaults.
// Rendering/network side effects are recorded but never fabricated.
const stage=document.querySelector('#stage');
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
let spec=null;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function configItem(){return spec?.windows?.find(item=>item.field==='ConfigBox')||null}
function bool(value){return value===true||String(value).toLowerCase()==='true'}
function setCheck(element,value){if(!element)return;element.dataset.sourceChecked=String(Boolean(value));const image=element.querySelector(':scope > img');if(image)image.src=asset('GameInter',value?162:161)}
function readCheck(element){if(!element)return false;const image=element.querySelector(':scope > img');if(image)return /GameInter\/00162\.png$/.test(image.src);return bool(element.dataset.sourceChecked)}
function selectedLabel(combo){return combo?.querySelector?.(':scope > .source-combo-selected-label,:scope > span')||null}
function setComboDefault(combo,value){
  if(!combo||value===undefined||value===null)return;
  const text=Array.isArray(value)&&value.length===2?`${value[0]} x ${value[1]}`:String(value);
  const label=selectedLabel(combo);if(label)label.textContent=text;
  combo.dataset.sourceConfigDefault=Array.isArray(value)?JSON.stringify(value):text;
}
function setDynamicEnabled(element,value){if(!element)return;element.dataset.sourceDynamicEnabled=String(Boolean(value));element.dispatchEvent(new CustomEvent('origins:source-enabled-changed',{bubbles:true}))}
function nestedByClass(className){return spec?.nestedWindows?.find(item=>item.sourceClass===className)||null}
function toggleNested(className){
  const item=nestedByClass(className);if(!item)return null;
  const id=`w-${item.id}`;const existing=document.getElementById(id);if(existing){existing.remove();return null}
  document.querySelector(`[data-window-id="${CSS.escape(item.id)}"]`)?.click();return document.getElementById(id);
}
function applyTabOverride(root,name,visible,enabled=true){
  const tab=control(root,name);if(!tab)return;tab.hidden=!visible;tab.dataset.sourceTabButtonVisible=String(visible);tab.dataset.sourceDynamicEnabled=String(enabled);tab.dispatchEvent(new CustomEvent('origins:source-enabled-changed',{bubbles:true}));
  tab.querySelectorAll?.('.dx-tab-button').forEach(button=>button.hidden=!visible);
}
function engineAction(root,controlName,action){
  const element=control(root,controlName);if(!element||element.dataset.sourceConfigActionBound==='true')return;element.dataset.sourceConfigActionBound='true';
  element.addEventListener('click',()=>queueMicrotask(()=>{root.dataset.sourceLastConfigEngineAction=action;root.dataset.sourceConfigEngineActionExecuted='false'}));
}
function install(root){
  if(!root||root.id!=='w-config'||root.dataset.sourceConfigRuntime==='true'||!spec)return;
  const item=configItem();if(!item)return;root.dataset.sourceConfigRuntime='true';root.dataset.sourceConfigState='checked-in Config.cs defaults';root.dataset.sourceZirconIniInvented='false';root.dataset.sourceRenderingEnvironmentInvented='false';

  for(const sourceControl of item.controls||[]){
    const element=control(root,sourceControl.name);if(!element)continue;
    let soundValue=null,soundMuted=null;
    for(const binding of sourceControl.sourceConfigBindings||[]){
      const value=binding.default;element.dataset.sourceConfigProperty=binding.configProperty;element.dataset.sourceConfigBindingKind=binding.kind;
      root.dataset[`config${binding.configProperty}`]=Array.isArray(value)?JSON.stringify(value):String(value??'');
      if(binding.kind==='checked'&&typeof value==='boolean'){
        setCheck(element,value);
        if(element.dataset.sourceConfigCheckBound!=='true'){
          element.dataset.sourceConfigCheckBound='true';element.addEventListener('click',()=>queueMicrotask(()=>{const current=readCheck(element);element.dataset.sourceChecked=String(current);root.dataset[`config${binding.configProperty}`]=String(current)}));
        }
      } else if(binding.kind==='selected') setComboDefault(element,value);
      else if(binding.kind==='value'){
        element.dataset.sourceConfigValue=String(value??'');element.dataset.value=String(value??'');soundValue=value;const field=element.querySelector('.dx-number-value,.dx-sound-value');if(field&&value!==undefined)field.textContent=String(value);
      } else if(binding.kind==='muted') {element.dataset.sourceConfigMuted=String(Boolean(value));soundMuted=Boolean(value)}
    }
    if(sourceControl.type==='DXSoundBar'){
      element.dispatchEvent(new CustomEvent('origins:source-config-sound-default',{bubbles:false,detail:{value:soundValue??0,muted:soundMuted??false}}));
      if(element.dataset.sourceConfigSoundBound!=='true'){
        element.dataset.sourceConfigSoundBound='true';
        element.addEventListener('origins:source-sound-changed',event=>{
          for(const binding of sourceControl.sourceConfigBindings||[]){
            if(binding.kind==='value')root.dataset[`config${binding.configProperty}`]=String(event.detail?.value??0);
            else if(binding.kind==='muted')root.dataset[`config${binding.configProperty}`]=String(Boolean(event.detail?.muted));
          }
          root.dataset.sourceAudioEngineEffect='Config volume/mute updated locally; CEnvir audio engine side effect not executed';
          root.dataset.sourceAudioEngineEffectExecuted='false';
        });
      }
    }
    if(sourceControl.sourceEnabledInGameScene)setDynamicEnabled(element,true);
  }

  // GameScene's ConfigBox object initializer hides Network and explicitly keeps UI.
  applyTabOverride(root,'NetworkTab',false,false);applyTabOverride(root,'UITab',true,true);
  root.dataset.sourceActiveScene='GameScene';

  const keyBind=control(root,'KeyBindButton');
  if(keyBind&&keyBind.dataset.sourceKeyBindBound!=='true'){
    keyBind.dataset.sourceKeyBindBound='true';keyBind.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();toggleNested('DXKeyBindWindow')},true);
  }

  // Source-side effects that cannot truthfully execute in the browser reference.
  engineAction(root,'FullScreenCheckBox','RenderingPipelineManager.ToggleFullScreen() + CenterOnSelectedMonitor when leaving fullscreen');
  engineAction(root,'BorderlessCheckbox','Config.Borderless + RenderingPipelineManager.ResetDevice()');
  engineAction(root,'VSyncCheckBox','Config.VSync + RenderingPipelineManager.ResetDevice()');
  engineAction(root,'ClipMouseCheckBox','Config.ClipMouse');
  engineAction(root,'DebugLabelCheckBox','Config.DebugLabel');
  engineAction(root,'DisplayHelmetCheckBox','C.HelmetToggle (server)');
  engineAction(root,'ObservableCheckBox','safe-zone guarded C.ObservableSwitch (server)');

  const language=control(root,'LanguageComboBox');
  language?.addEventListener('origins:source-combo-selected',event=>{const option=event.detail?.option;root.dataset.configLanguage=String(option?.valueExpression??option?.label??'');root.dataset.sourceLanguageReload='CEnvir.LoadLanguage(); C.SelectLanguage only if connected';root.dataset.sourceLanguageReloadExecuted='false'});
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-config')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-config').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;install(document.querySelector('#w-config'));console.info('ORIGINS Config source runtime active: Config.cs defaults + GameScene enable/tab overrides + KeyBind + local sound state')}).catch(error=>console.error('Unable to load Config source manifest',error));
