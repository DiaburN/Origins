import test from 'node:test';
import assert from 'node:assert/strict';

import { resolvePlayerVisualComposition } from '../player-visual-runtime.js';

const BASE={
  drawFrame:40,
  direction:4,
  animation:'Standing',
  playerClass:'Warrior',
  gender:'Male',
  armourShape:0,
  costumeShape:-1,
  hairType:1,
  libraryWeaponShape:0,
  shieldShape:-1,
  horseShape:0,
  horseType:0,
  drawWeapon:true,
  hideHead:false,
};

function layers(overrides={}){
  return resolvePlayerVisualComposition({...BASE,...overrides});
}

test('no equipped gear draws body and appearance only',()=>{
  const c=layers({weaponEquipped:false,helmetShape:0,shieldShape:-1});
  assert.deepEqual(c.layers.map(x=>x.layer),['body','hair']);
  assert.deepEqual(c.layers.map(x=>x.libraryFile),['M_Hum','M_Hair']);
  assert.deepEqual(c.equipment,{weapon:false,helmet:false,shield:false,mounted:false});
});

test('weapon shape alone does not invent an equipped weapon',()=>{
  const c=layers({libraryWeaponShape:0,weaponEquipped:false});
  assert.ok(!c.layers.some(x=>x.layer==='weapon1'||x.layer==='weapon2'));
  assert.equal(c.equipment.weapon,false);
});

test('equipped weapon draws only when the animation permits DrawWeapon',()=>{
  const visible=layers({weaponEquipped:true});
  assert.deepEqual(visible.layers.map(x=>x.layer),['body','hair','weapon1']);
  assert.equal(visible.layers.at(-1).libraryFile,'M_Weapon1');

  const hidden=layers({weaponEquipped:true,drawWeapon:false});
  assert.deepEqual(hidden.layers.map(x=>x.layer),['body','hair']);
  assert.equal(hidden.equipment.weapon,true);
});

test('helmet is visible only for HelmetShape > 0 and replaces hair',()=>{
  const c=layers({helmetShape:1});
  assert.deepEqual(c.layers.map(x=>x.layer),['body','helmet']);
  assert.equal(c.layers[1].libraryFile,'M_Helmet1');
  assert.equal(c.equipment.helmet,true);
});

test('shield is absent at -1 and visible at shape 0',()=>{
  const absent=layers({shieldShape:-1});
  assert.ok(!absent.layers.some(x=>x.layer==='shield'));
  assert.equal(absent.equipment.shield,false);

  const equipped=layers({shieldShape:0});
  assert.deepEqual(equipped.layers.map(x=>x.layer),['body','hair','shield']);
  assert.equal(equipped.layers.at(-1).libraryFile,'M_Shield1');
  assert.equal(equipped.equipment.shield,true);
});

test('full equipped stack is explicit and does not include hair under helmet',()=>{
  const c=layers({weaponEquipped:true,helmetShape:1,shieldShape:0});
  assert.deepEqual(c.layers.map(x=>x.layer),['body','helmet','weapon1','shield']);
  assert.deepEqual(c.layers.map(x=>x.libraryFile),['M_Hum','M_Helmet1','M_Weapon1','M_Shield1']);
  assert.deepEqual(c.equipment,{weapon:true,helmet:true,shield:true,mounted:false});
});
