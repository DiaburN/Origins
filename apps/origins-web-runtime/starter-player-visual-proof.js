import { resolvePlayerVisualComposition } from './player-visual-runtime.js';
import { PLAYER_ASSET_STATUS, ZirconPlayerSpriteStore, drawResolvedFrame } from './player-sprite-runtime.js';

const canvas=document.querySelector('#proof');
const ctx=canvas.getContext('2d',{alpha:false});
const resultNode=document.querySelector('#result');
const params=new URLSearchParams(location.search);
const gender=params.get('gender')==='Female'?'Female':'Male';
const store=new ZirconPlayerSpriteStore({rootUrl:'./assets/player/'});
const direction=4; // MirDirection.Down
const drawFrame=40; // Standing start 0 + offset 10 * Down(4) + local frame 0

const EXPECTED_BY_GENDER={
  Male:['M_Hum','M_Hair','M_Weapon1','M_Helmet1','M_Shield1'],
  Female:['WM_Hum','WM_Hair','WM_Weapon1','WM_Helmet1','WM_Shield1'],
};

function composition({helmetShape,hairType}){
  return resolvePlayerVisualComposition({
    drawFrame,
    direction,
    animation:'Standing',
    playerClass:'Warrior',
    gender,
    armourShape:0,
    costumeShape:-1,
    helmetShape,
    hairType,
    libraryWeaponShape:0,
    weaponEquipped:true,
    shieldShape:0,
    horseShape:0,
    horseType:0,
    drawWeapon:true,
    hideHead:false,
  });
}

function setDataset(values){
  const d=document.documentElement.dataset;
  for(const [key,value] of Object.entries(values)) d[key]=String(value);
}

function background(){
  ctx.fillStyle='#121416';ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle='#25292b';ctx.lineWidth=1;
  for(let x=0;x<canvas.width;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,canvas.height);ctx.stroke();}
  for(let y=0;y<canvas.height;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(canvas.width,y);ctx.stroke();}
  ctx.fillStyle='#e7c875';ctx.font='bold 16px ui-monospace,monospace';ctx.fillText(`${gender} — pinned Zircon`,24,34);
  ctx.fillStyle='#aaa397';ctx.font='13px ui-monospace,monospace';
  ctx.fillText('EQUIPPED: HAIR + WEAPON + SHIELD',95,72);ctx.fillText('EQUIPPED: HELMET + WEAPON + SHIELD',455,72);
}

async function drawComposition(comp,anchorX,anchorY){
  const resolved=[];
  for(const layer of comp.layers){
    const frame=await store.getFrame(layer.libraryFile,layer.imageIndex);
    if(!frame) throw new Error(`${layer.layer}: missing ${layer.libraryFile} image ${layer.imageIndex}`);
    resolved.push({layer,frame});
  }
  for(const row of resolved) drawResolvedFrame(ctx,row.frame,anchorX,anchorY);
  return resolved.map(row=>`${row.layer.layer}:${row.layer.libraryFile}`);
}

async function run(){
  try{
    background();
    const status=await store.load();
    if(status!==PLAYER_ASSET_STATUS.Ready) throw new Error(`asset store status ${status}`);
    const expected=EXPECTED_BY_GENDER[gender];
    const absent=expected.filter(name=>!store.hasLibrary(name));
    if(absent.length) throw new Error(`missing required libraries: ${absent.join(', ')}`);

    const hair=composition({helmetShape:0,hairType:1});
    const helmet=composition({helmetShape:1,hairType:1});
    const hairLayers=await drawComposition(hair,245,285);
    const helmetLayers=await drawComposition(helmet,615,285);

    const hairNames=hair.layers.map(x=>x.libraryFile);
    const helmetNames=helmet.layers.map(x=>x.libraryFile);
    const requiredHair=[expected[0],expected[1],expected[2],expected[4]];
    const requiredHelmet=[expected[0],expected[3],expected[2],expected[4]];
    for(const name of requiredHair) if(!hairNames.includes(name)) throw new Error(`hair composition omitted ${name}`);
    for(const name of requiredHelmet) if(!helmetNames.includes(name)) throw new Error(`helmet composition omitted ${name}`);
    if(!hair.equipment.weapon||!hair.equipment.shield||hair.equipment.helmet) throw new Error('hair equipment state mismatch');
    if(!helmet.equipment.weapon||!helmet.equipment.shield||!helmet.equipment.helmet) throw new Error('helmet equipment state mismatch');

    const report={
      status:'PASS',gender,direction,drawFrame,
      hairEquipment:hair.equipment,
      helmetEquipment:helmet.equipment,
      hairComposition:hair.layers.map(x=>({layer:x.layer,libraryFile:x.libraryFile,imageIndex:x.imageIndex,phase:x.phase})),
      helmetComposition:helmet.layers.map(x=>({layer:x.layer,libraryFile:x.libraryFile,imageIndex:x.imageIndex,phase:x.phase})),
    };
    resultNode.textContent=JSON.stringify(report,null,2);
    setDataset({
      starterVisualStatus:'PASS',
      starterVisualGender:gender,
      starterVisualDrawFrame:drawFrame,
      starterVisualHairLibraries:hairNames.join(','),
      starterVisualHelmetLibraries:helmetNames.join(','),
      starterVisualHairLayerCount:hairLayers.length,
      starterVisualHelmetLayerCount:helmetLayers.length,
      starterVisualWeaponEquipped:'true',
      starterVisualShieldEquipped:'true',
    });
  }catch(error){
    const message=error instanceof Error?error.message:String(error);
    resultNode.textContent=`FAIL: ${message}`;
    setDataset({starterVisualStatus:'FAIL',starterVisualGender:gender,starterVisualError:message});
  }
}

void run();
