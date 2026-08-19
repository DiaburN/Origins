// Source-faithful GuildDialog no-guild neutral state. Guild/member/storage/castle
// payloads and player gold are runtime-only and are never fabricated.
const stage=document.querySelector('#stage');
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
const CREATION=7500000,MEMBER_COST=1000000,STORAGE_COST=350000;
function byName(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function bySuffix(root,suffix){return [...(root?.querySelectorAll?.('[data-control-name]')||[])].find(el=>String(el.dataset.controlName||'').endsWith(suffix))||null}
function setVisible(el,value){if(!el)return;el.hidden=!value;el.dataset.sourceDynamicVisible=String(value)}
function setChecked(box,value){if(!box)return;box.dataset.sourceChecked=String(Boolean(value));const image=box.querySelector(':scope > img');if(image)image.src=asset('GameInter',value?162:161)}
function setEnabled(el,value){if(!el)return;el.dataset.sourceDynamicEnabled=String(Boolean(value));el.dispatchEvent(new CustomEvent('origins:source-enabled-changed',{bubbles:true}))}
function setNumber(box,value){if(!box)return;box.dataset.value=String(value);const field=box.querySelector('.dx-number-value');if(field)field.textContent=String(value);else box.textContent=String(value)}
function setBackground(root,index){const bg=byName(root,'BackgroundImage');if(!bg)return;const image=bg instanceof HTMLImageElement?bg:bg.querySelector('img');if(image)image.src=asset('Interface',index);bg.dataset.sourceDynamicIndex=String(index)}
function recalc(root){
  const gold=byName(root,'GoldCheckBox')?.dataset.sourceChecked!=='false';const members=Number(byName(root,'MemberTextBox')?.dataset.value||0)||0;const storage=Number(byName(root,'StorageTextBox')?.dataset.value||0)||0;
  const total=Math.min(2147483647,(gold?CREATION:0)+members*MEMBER_COST+storage*STORAGE_COST);setNumber(byName(root,'TotalCostBox'),total);root.dataset.sourceGuildTotalCost=String(total);root.dataset.sourceGuildCanCreate='false: GameScene.Game.User.Gold runtime unavailable';setEnabled(byName(root,'CreateButton'),false);
}
function install(root){
  if(!root||root.id!=='w-guild'||root.dataset.sourceGuildRuntime==='true')return;root.dataset.sourceGuildRuntime='true';root.dataset.sourceGuildInfo='null';root.dataset.sourceGuildState='no-guild/CreateTab';root.dataset.sourceGuildDataInvented='false';root.dataset.sourceGuildCreationCost=String(CREATION);root.dataset.sourceGuildMemberCost=String(MEMBER_COST);root.dataset.sourceGuildStorageCost=String(STORAGE_COST);

  // ClearGuild() then GuildInfo=null invokes CreateTab, which changes 261 -> 266.
  setBackground(root,266);
  for(const [name,visible] of [['CreatePanel',true],['AddMemberPanel',false],['TreasuryPanel',false],['StoragePanel',false],['WarPanel',false],['CastlePanel',false]])setVisible(byName(root,name),visible);
  for(const name of ['HomeTab','MemberTab','StorageTab','WarTab','StyleTab','CastleTab']){
    const tab=byName(root,name);if(tab){tab.dataset.sourceTabButtonVisible='false';tab.hidden=true}
  }
  const createTab=byName(root,'CreateTab');if(createTab){createTab.dataset.sourceTabButtonVisible='true';createTab.hidden=false}

  const gold=byName(root,'GoldCheckBox'),horn=byName(root,'HornCheckBox');
  for(const box of [gold,horn].filter(Boolean)){box.dataset.sourceReadonlyCustomClick='true';box.dataset.sourceReadOnly='true'}
  setChecked(gold,true);setChecked(horn,false);
  gold?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();setChecked(gold,true);setChecked(horn,false);recalc(root)},true);
  horn?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();setChecked(horn,true);setChecked(gold,false);recalc(root)},true);

  setNumber(byName(root,'MemberTextBox'),0);setNumber(byName(root,'StorageTextBox'),0);recalc(root);
  const guildName=byName(root,'GuildNameBox');
  if(guildName){guildName.contentEditable='true';guildName.spellcheck=false;guildName.dataset.sourceGuildNameRegex='^[A-Za-z0-9]{2,15}$';guildName.addEventListener('input',()=>{const name=(guildName.textContent||'').trim();const valid=/^[A-Za-z0-9]{2,15}$/.test(name);root.dataset.sourceGuildNameValid=String(valid);guildName.dataset.sourceBorderColour=valid?'Green':name?'Red':'Constants.PrimaryColour';recalc(root)})}
  byName(root,'CreateButton')?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();root.dataset.sourceGuildCreateAction='C.GuildCreate requires valid name + real GameScene.User.Gold';root.dataset.sourceGuildCreateActionExecuted='false'},true);
  byName(root,'StarterGuildButton')?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();root.dataset.sourceStarterGuildAction='C.JoinStarterGuild';root.dataset.sourceStarterGuildActionExecuted='false'},true);
  root.dataset.sourceGuildStorage='runtime GuildInfo/packets; neutral grid 1x1';root.dataset.sourceGuildMembers='runtime ClientGuildInfo';root.dataset.sourceGuildCastles='runtime ClientGuildInfo.Castles';
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-guild')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-guild').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-guild'));
console.info('ORIGINS Guild source runtime active: no-guild CreateTab/#266, Gold cost 7.5m, runtime guild/user data neutral');
