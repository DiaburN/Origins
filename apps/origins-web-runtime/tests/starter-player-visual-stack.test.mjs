import test from 'node:test';
import assert from 'node:assert/strict';

import { resolvePlayerVisualComposition } from '../player-visual-runtime.js';

const BASE={
  drawFrame:40,
  direction:4,
  animation:'Standing',
  playerClass:'Warrior',
  armourShape:0,
  costumeShape:-1,
  libraryWeaponShape:0,
  shieldShape:0,
  horseShape:0,
  horseType:0,
  drawWeapon:true,
  hideHead:false,
};

for(const gender of ['Male','Female']){
  const prefix=gender==='Male'?'M':'WM';

  test(`${gender} starter hair stack matches pinned Zircon Down draw order`,()=>{
    const c=resolvePlayerVisualComposition({...BASE,gender,helmetShape:0,hairType:1});
    assert.deepEqual(c.layers.map(x=>x.layer),['body','hair','weapon1','shield']);
    assert.deepEqual(c.layers.map(x=>x.phase),['body','body','front','front']);
    assert.deepEqual(c.layers.map(x=>x.libraryFile),[
      `${prefix}_Hum`,`${prefix}_Hair`,`${prefix}_Weapon1`,`${prefix}_Shield1`,
    ]);
    assert.deepEqual(c.layers.map(x=>x.imageIndex),[40,40,40,40]);
  });

  test(`${gender} starter helmet stack replaces hair and keeps weapon shield order`,()=>{
    const c=resolvePlayerVisualComposition({...BASE,gender,helmetShape:1,hairType:1});
    assert.deepEqual(c.layers.map(x=>x.layer),['body','helmet','weapon1','shield']);
    assert.deepEqual(c.layers.map(x=>x.phase),['body','body','front','front']);
    assert.deepEqual(c.layers.map(x=>x.libraryFile),[
      `${prefix}_Hum`,`${prefix}_Helmet1`,`${prefix}_Weapon1`,`${prefix}_Shield1`,
    ]);
    assert.deepEqual(c.layers.map(x=>x.imageIndex),[40,40,40,40]);
    assert.ok(!c.layers.some(x=>x.layer==='hair'));
  });
}
