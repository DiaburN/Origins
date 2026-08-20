import test from 'node:test';
import assert from 'node:assert/strict';

import { resolvePlayerLibrarySelection } from '../player-animation-runtime.js';

const EXPECTED={
  0:['Horse',null,null],
  1:['Horse','HorseIron',null],
  2:['Horse','HorseSilver',null],
  3:['Horse','HorseGold',null],
  4:['Horse','HorseBlue',null],
  5:['Horse','HorseDark','HorseDarkEffect'],
  6:['Horse','HorseRoyal','HorseRoyalEffect'],
  7:['Horse','HorseBlueDragon','HorseBlueDragonEffect'],
};

for(const [shape,expected] of Object.entries(EXPECTED)){
  test(`horse shape ${shape} resolves pinned Zircon base/shape/effect libraries`,()=>{
    const libraries=resolvePlayerLibrarySelection({
      playerClass:'Warrior',gender:'Male',armourShape:0,costumeShape:-1,
      helmetShape:0,libraryWeaponShape:0,shieldShape:-1,horseShape:Number(shape),
    });
    assert.deepEqual(
      [libraries.horseBase,libraries.horseShape,libraries.horseShapeEffect],
      expected,
    );
  });
}
