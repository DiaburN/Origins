# ORIGINS-DxR — Auditoría final de magias Zircon

- Fuente: `Suprcode/Zircon` @ `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Definición de jugable: `ENUM_DEFINED + exactly one MagicInfo row + exactly one registered MagicObject handler`
- Crystal / Crystal-Monk: **fuera del runtime y fuera de esta auditoría**.
- `LevelDelayReduction`: **NO EXISTE** en el `MagicInfo` del Zircon fijado; valor reportado = `N/A`. MagicInfo.LevelDelayReduction does not exist in pinned Zircon cbf1aa919083bc13fc3f23f93772a8ab8370632d; ORIGINS-DxR does not invent or restore it.

## Resumen real

| Clase | Enum | MagicInfo DB | Handlers | Jugables | Enum only | DB sin handler | Handler sin DB | NOT CODED | UNUSED |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Warrior | 38 | 32 | 37 | 32 | 0 | 0 | 5 | 1 | 0 |
| Wizard | 47 | 42 | 46 | 40 | 0 | 0 | 4 | 3 | 0 |
| Taoist | 52 | 47 | 51 | 47 | 0 | 0 | 4 | 1 | 0 |
| Assassin | 58 | 53 | 56 | 52 | 0 | 0 | 4 | 1 | 1 |
| TOTAL | 195 | 174 | 190 | 171 | 0 | 0 | 17 | 6 | 1 |

## Criterio

Una entrada solo figura como `PLAYABLE` cuando está `ENUM_DEFINED`, tiene exactamente una fila `MagicInfo` de la clase y exactamente un handler registrado por la regla nativa de `SEnvir.CreateMagic`. Las entradas `UPSTREAM_NOT_CODED` y `UPSTREAM_UNUSED` nunca se promocionan a jugables aunque exista material parcial.

## WARRIOR

Enum **38** · DB **32** · handlers **37** · jugables **32** · enum-only **0** · DB sin handler **0** · handler sin DB **5** · NOT CODED **1** · UNUSED **0**.

| MagicType | Nombre | Estado | DB idx | Icon | School | Property | Need L1/L2/L3 | Exp 1/2/3 | Base/Level Cost | Delay | Powers | Handler |
|---:|---|---|---:|---:|---:|---:|---|---|---|---:|---|---|
| 100 | Swordsmanship | PLAYABLE | 1 | 4 | 1 | 2 | 7/9/11 | 100/200/300 | 0/0 | 0 | B 0-0; L 10-10 | Swordsmanship (ServerLibrary/Models/Magics/Warrior/Swordsmanship.cs) |
| 101 | PotionMastery | PLAYABLE | 2 | 262 | 1 | 2 | 12/22/33 | 10000/20000/40000 | 0/0 | 0 | B 10-10; L 15-15 | PotionMastery (ServerLibrary/Models/Magics/Warrior/PotionMastery.cs) |
| 102 | Slaying | PLAYABLE | 3 | 12 | 1 | 2 | 14/16/18 | 300/400/500 | 0/0 | 0 | B 8-8; L 7-7 | Slaying (ServerLibrary/Models/Magics/Warrior/Slaying.cs) |
| 103 | Thrusting | PLAYABLE | 4 | 22 | 3 | 4 | 19/21/23 | 400/500/600 | 0/0 | 0 | B 50-50; L 50-50 | Thrusting (ServerLibrary/Models/Magics/Warrior/Thrusting.cs) |
| 104 | HalfMoon | PLAYABLE | 5 | 48 | 3 | 4 | 24/26/28 | 600/700/800 | 3/0 | 0 | B 40-40; L 50-50 | HalfMoon (ServerLibrary/Models/Magics/Warrior/HalfMoon.cs) |
| 105 | ShoulderDash | PLAYABLE | 6 | 52 | 2 | 1 | 27/29/31 | 700/800/900 | 0/20 | 4000 | B 2-3; L 3-3 | ShoulderDash (ServerLibrary/Models/Magics/Warrior/ShoulderDash.cs) |
| 106 | FlamingSword | PLAYABLE | 7 | 50 | 2 | 5 | 32/34/36 | 1000/1100/1200 | 7/2 | 7000 | B 160-160; L 100-100 | FlamingSword (ServerLibrary/Models/Magics/Warrior/FlamingSword.cs) |
| 107 | DragonRise | PLAYABLE | 8 | 68 | 2 | 5 | 35/37/39 | 1000/1100/1200 | 8/2 | 7000 | B 120-120; L 100-100 | DragonRise (ServerLibrary/Models/Magics/Warrior/DragonRise.cs) |
| 108 | BladeStorm | PLAYABLE | 9 | 66 | 2 | 5 | 38/40/42 | 1000/1100/1200 | 9/3 | 7000 | B 240-240; L 100-100 | BladeStorm (ServerLibrary/Models/Magics/Warrior/BladeStorm.cs) |
| 109 | DestructiveSurge | PLAYABLE | 10 | 204 | 3 | 4 | 40/43/46 | 2000/3000/6000 | 7/0 | 0 | B 70-70; L 30-30 | DestructiveSurge (ServerLibrary/Models/Magics/Warrior/DestructiveSurge.cs) |
| 110 | Interchange | PLAYABLE | 11 | 212 | 2 | 1 | 42/45/48 | 4000/6000/12000 | 10/40 | 5000 | B 0-0; L 0-0 | Interchange (ServerLibrary/Models/Magics/Warrior/Interchange.cs) |
| 111 | Defiance | PLAYABLE | 12 | 202 | 2 | 1 | 44/47/50 | 6000/9000/18000 | 40/80 | 0 | B 30-30; L 90-90 | Defiance (ServerLibrary/Models/Magics/Warrior/Defiance.cs) |
| 112 | Beckon | PLAYABLE | 13 | 214 | 2 | 1 | 46/49/52 | 8000/12000/24000 | 20/40 | 5000 | B 0-0; L 0-0 | Beckon (ServerLibrary/Models/Magics/Warrior/Beckon.cs) |
| 113 | Might | PLAYABLE | 14 | 210 | 2 | 1 | 48/51/54 | 10000/15000/30000 | 50/100 | 0 | B 30-30; L 90-90 | Might (ServerLibrary/Models/Magics/Warrior/Might.cs) |
| 114 | SwiftBlade | PLAYABLE | 15 | 260 | 2 | 1 | 49/57/65 | 12000/16000/32000 | 50/80 | 7000 | B 80-80; L 100-100 | SwiftBlade (ServerLibrary/Models/Magics/Warrior/SwiftBlade.cs) |
| 115 | Assault | PLAYABLE | 16 | 216 | 2 | 3 | 50/53/56 | 10000/15000/30000 | 0/50 | 8000 | B 1000-1000; L 2000-2000 | Assault (ServerLibrary/Models/Magics/Warrior/Assault.cs) |
| 116 | Endurance | PLAYABLE | 17 | 254 | 2 | 1 | 51/55/59 | 10000/18000/32000 | 20/40 | 120000 | B 10-10; L 10-10 | Endurance (ServerLibrary/Models/Magics/Warrior/Endurance.cs) |
| 117 | ReflectDamage | PLAYABLE | 18 | 250 | 2 | 1 | 53/58/63 | 10000/18000/32000 | 10/10 | 120000 | B 35-35; L 40-40 | ReflectDamage (ServerLibrary/Models/Magics/Warrior/ReflectDamage.cs) |
| 118 | Fetter | PLAYABLE | 19 | 258 | 2 | 1 | 55/61/67 | 20000/30000/40000 | 35/55 | 0 | B 5000-5000; L 7000-7000 | Fetter (ServerLibrary/Models/Magics/Warrior/Fetter.cs) |
| 119 | AugmentDestructiveSurge | PLAYABLE | 20 | 526 | 3 | 3 | 84/90/96 | 20000/30000/60000 | 0/0 | 0 | B 15-15; L 5-5 | AugmentDestructiveSurge (ServerLibrary/Models/Magics/Warrior/AugmentDestructiveSurge.cs) |
| 120 | AugmentDefiance | PLAYABLE | 21 | 388 | 1 | 3 | 80/82/84 | 3000/4500/9000 | 0/0 | 0 | B 0-0; L 0-0 | AugmentDefiance (ServerLibrary/Models/Magics/Warrior/AugmentDefiance.cs) |
| 121 | AugmentReflectDamage | PLAYABLE | 22 | 458 | 1 | 3 | 82/82/82 | 20000/40000/60000 | 0/0 | 0 | B 1-1; L 1-1 | AugmentReflectDamage (ServerLibrary/Models/Magics/Warrior/AugmentReflectDamage.cs) |
| 122 | AdvancedPotionMastery | PLAYABLE | 135 | 262 | 0 | 3 | 40/50/60 | 20000/40000/80000 | 0/0 | 0 | B 10-10; L 15-15 | AdvancedPotionMastery (ServerLibrary/Models/Magics/Warrior/AdvancedPotionMastery.cs) |
| 123 | MassBeckon | PLAYABLE | 138 | 386 | 2 | 1 | 60/63/66 | 5000/10000/25000 | 100/50 | 5000 | B 0-0; L 0-0 | MassBeckon (ServerLibrary/Models/Magics/Warrior/MassBeckon.cs) |
| 124 | SeismicSlam | PLAYABLE | 142 | 434 | 2 | 1 | 83/85/87 | 10000/20000/30000 | 50/100 | 18000 | B 120-120; L 150-150 | SeismicSlam (ServerLibrary/Models/Magics/Warrior/SeismicSlam.cs) |
| 125 | Invincibility | PLAYABLE | 146 | 442 | 2 | 1 | 65/70/75 | 1200/1800/3000 | 0/100 | 5000 | B 0-30; L 20-20 | Invincibility (ServerLibrary/Models/Magics/Warrior/Invincibility.cs) |
| 126 | CrushingWave | PLAYABLE | 147 | 450 | 2 | 1 | 90/90/90 | 10000/20000/30000 | 0/100 | 0 | B 0-30; L 20-20 | CrushingWave (ServerLibrary/Models/Magics/Warrior/CrushingWave.cs) |
| 127 | DefensiveMastery | PLAYABLE | 152 | 466 | 1 | 2 | 70/75/80 | 10000/20000/40000 | 0/0 | 0 | B 1-1; L 1-1 | DefensiveMastery (ServerLibrary/Models/Magics/Warrior/DefensiveMastery.cs) |
| 128 | PhysicalImmunity | PLAYABLE | 153 | 468 | 1 | 2 | 80/84/88 | 10000/20000/40000 | 0/0 | 0 | B 1-6; L 1-1 | PhysicalImmunity (ServerLibrary/Models/Magics/Warrior/PhysicalImmunity.cs) |
| 129 | MagicImmunity | PLAYABLE | 154 | 470 | 1 | 2 | 80/84/88 | 10000/20000/40000 | 0/0 | 0 | B 1-6; L 1-1 | MagicImmunity (ServerLibrary/Models/Magics/Warrior/MagicImmunity.cs) |
| 130 | DefensiveBlow | PLAYABLE | 155 | 488 | 2 | 5 | 86/88/91 | 15000/20000/30000 | 50/0 | 10000 | B 10-10; L 10-10 | DefensiveBlow (ServerLibrary/Models/Magics/Warrior/DefensiveBlow.cs) |
| 131 | ElementalSwords | PLAYABLE | 156 | 502 | 2 | 1 | 95/96/97 | 10000/20000/30000 | 10/5 | 5000 | B 5-15; L 5-10 | ElementalSwords (ServerLibrary/Models/Magics/Warrior/ElementalSwords.cs) |
| 132 | Shuriken | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | Shuriken (ServerLibrary/Models/Magics/Warrior/Shuriken.cs) |
| 133 | HundredFist | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | HundredFist (ServerLibrary/Models/Magics/Warrior/HundredFist.cs) |
| 134 | OffensiveBlow | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | OffensiveBlow (ServerLibrary/Models/Magics/Warrior/OffensiveBlow.cs) |
| 135 | TaecheonSword | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | TaecheonSword (ServerLibrary/Models/Magics/Warrior/TaecheonSword.cs) |
| 136 | FireSword | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | FireSword (ServerLibrary/Models/Magics/Warrior/FireSword.cs) |
| 137 | FlameArt | NOT CODED | — | — | — | — | — | — | — | — | — | — |

## WIZARD

Enum **47** · DB **42** · handlers **46** · jugables **40** · enum-only **0** · DB sin handler **0** · handler sin DB **4** · NOT CODED **3** · UNUSED **0**.

| MagicType | Nombre | Estado | DB idx | Icon | School | Property | Need L1/L2/L3 | Exp 1/2/3 | Base/Level Cost | Delay | Powers | Handler |
|---:|---|---|---:|---:|---:|---:|---|---|---|---:|---|---|
| 201 | FireBall | PLAYABLE | 23 | 0 | 4 | 1 | 7/9/11 | 100/200/300 | 1/3 | 0 | B 0-4; L 6-10 | FireBall (ServerLibrary/Models/Magics/Wizard/FireBall.cs) |
| 202 | LightningBall | PLAYABLE | 24 | 80 | 6 | 1 | 8/10/12 | 100/200/300 | 1/4 | 0 | B 0-4; L 6-10 | LightningBall (ServerLibrary/Models/Magics/Wizard/LightningBall.cs) |
| 203 | IceBolt | PLAYABLE | 25 | 76 | 5 | 1 | 9/11/13 | 100/200/300 | 1/4 | 0 | B 0-4; L 4-8 | IceBolt (ServerLibrary/Models/Magics/Wizard/IceBolt.cs) |
| 204 | GustBlast | PLAYABLE | 26 | 132 | 7 | 1 | 10/12/14 | 100/200/300 | 1/3 | 0 | B 0-4; L 5-9 | GustBlast (ServerLibrary/Models/Magics/Wizard/GustBlast.cs) |
| 205 | Repulsion | PLAYABLE | 27 | 14 | 7 | 1 | 12/14/16 | 200/300/400 | 1/8 | 0 | B 2-3; L 3-3 | Repulsion (ServerLibrary/Models/Magics/Wizard/Repulsion.cs) |
| 206 | ElectricShock | PLAYABLE | 28 | 38 | 6 | 1 | 13/15/17 | 200/300/400 | 3/3 | 0 | B 0-0; L 0-0 | ElectricShock (ServerLibrary/Models/Magics/Wizard/ElectricShock.cs) |
| 207 | Teleportation | PLAYABLE | 29 | 40 | 10 | 1 | 14/16/18 | 300/400/500 | 10/10 | 7000 | B 0-0; L 0-0 | Teleportation (ServerLibrary/Models/Magics/Wizard/Teleportation.cs) |
| 208 | AdamantineFireBall | PLAYABLE | 30 | 8 | 4 | 1 | 15/17/19 | 400/500/600 | 6/6 | 0 | B 7-11; L 15-19 | AdamantineFireBall (ServerLibrary/Models/Magics/Wizard/AdamantineFireBall.cs) |
| 209 | ThunderBolt | PLAYABLE | 31 | 20 | 6 | 1 | 16/18/20 | 400/500/600 | 6/7 | 0 | B 7-11; L 15-19 | ThunderBolt (ServerLibrary/Models/Magics/Wizard/ThunderBolt.cs) |
| 210 | IceBlades | PLAYABLE | 32 | 78 | 5 | 1 | 17/19/21 | 400/500/600 | 6/7 | 0 | B 7-11; L 13-17 | IceBlades (ServerLibrary/Models/Magics/Wizard/IceBlades.cs) |
| 211 | Cyclone | PLAYABLE | 33 | 146 | 7 | 1 | 18/20/22 | 400/500/600 | 6/6 | 0 | B 7-11; L 14-18 | Cyclone (ServerLibrary/Models/Magics/Wizard/Cyclone.cs) |
| 212 | ScortchedEarth | PLAYABLE | 34 | 16 | 4 | 1 | 20/22/24 | 500/600/700 | 15/11 | 0 | B 12-16; L 14-18 | ScortchedEarth (ServerLibrary/Models/Magics/Wizard/ScortchedEarth.cs) |
| 213 | LightningBeam | PLAYABLE | 35 | 18 | 6 | 1 | 21/23/25 | 500/600/700 | 15/12 | 0 | B 12-16; L 14-14 | LightningBeam (ServerLibrary/Models/Magics/Wizard/LightningBeam.cs) |
| 214 | FrozenEarth | PLAYABLE | 36 | 104 | 5 | 1 | 22/24/26 | 500/600/700 | 15/12 | 0 | B 12-16; L 12-16 | FrozenEarth (ServerLibrary/Models/Magics/Wizard/FrozenEarth.cs) |
| 215 | BlowEarth | PLAYABLE | 37 | 144 | 7 | 1 | 23/25/27 | 600/700/800 | 15/13 | 0 | B 12-16; L 13-17 | BlowEarth (ServerLibrary/Models/Magics/Wizard/BlowEarth.cs) |
| 216 | FireWall | PLAYABLE | 38 | 42 | 4 | 1 | 24/26/28 | 600/700/800 | 30/22 | 0 | B 1-6; L 2-9 | FireWall (ServerLibrary/Models/Magics/Wizard/FireWall.cs) |
| 217 | ExpelUndead | PLAYABLE | 39 | 62 | 10 | 1 | 26/28/30 | 700/800/900 | 30/30 | 0 | B 0-0; L 0-0 | ExpelUndead (ServerLibrary/Models/Magics/Wizard/ExpelUndead.cs) |
| 218 | GeoManipulation | PLAYABLE | 40 | 206 | 10 | 1 | 27/29/31 | 800/900/1000 | 20/25 | 5000 | B 0-0; L 0-0 | GeoManipulation (ServerLibrary/Models/Magics/Wizard/GeoManipulation.cs) |
| 219 | MagicShield | PLAYABLE | 41 | 60 | 10 | 1 | 29/31/33 | 900/1000/1100 | 30/20 | 0 | B 0-0; L 0-0 | MagicShield (ServerLibrary/Models/Magics/Wizard/MagicShield.cs) |
| 220 | FireStorm | PLAYABLE | 42 | 44 | 4 | 1 | 32/34/36 | 1000/1100/1200 | 20/15 | 0 | B 14-18; L 14-18 | FireStorm (ServerLibrary/Models/Magics/Wizard/FireStorm.cs) |
| 221 | LightningWave | PLAYABLE | 43 | 46 | 6 | 1 | 33/35/37 | 1000/1100/1200 | 20/17 | 0 | B 14-18; L 14-18 | LightningWave (ServerLibrary/Models/Magics/Wizard/LightningWave.cs) |
| 222 | IceStorm | PLAYABLE | 44 | 64 | 5 | 1 | 34/36/38 | 1000/1100/1200 | 20/19 | 0 | B 14-18; L 12-16 | IceStorm (ServerLibrary/Models/Magics/Wizard/IceStorm.cs) |
| 223 | DragonTornado | PLAYABLE | 45 | 142 | 7 | 1 | 35/37/39 | 1000/1100/1200 | 20/18 | 0 | B 14-18; L 13-17 | DragonTornado (ServerLibrary/Models/Magics/Wizard/DragonTornado.cs) |
| 224 | GreaterFrozenEarth | PLAYABLE | 46 | 218 | 5 | 1 | 38/41/44 | 1000/1500/3000 | 20/20 | 0 | B 16-20; L 16-20 | GreaterFrozenEarth (ServerLibrary/Models/Magics/Wizard/GreaterFrozenEarth.cs) |
| 225 | ChainLightning | PLAYABLE | 47 | 220 | 6 | 1 | 40/42/44 | 2000/3000/6000 | 30/40 | 0 | B 20-30; L 20-40 | ChainLightning (ServerLibrary/Models/Magics/Wizard/ChainLightning.cs) |
| 226 | MeteorShower | PLAYABLE | 48 | 224 | 4 | 1 | 43/45/47 | 5000/7500/15000 | 40/38 | 0 | B 14-22; L 32-40 | MeteorShower (ServerLibrary/Models/Magics/Wizard/MeteorShower.cs) |
| 227 | Renounce | PLAYABLE | 49 | 222 | 10 | 1 | 46/48/50 | 8000/12000/24000 | 10/60 | 0 | B 0-0; L 0-0 | Renounce (ServerLibrary/Models/Magics/Wizard/Renounce.cs) |
| 228 | Tempest | PLAYABLE | 50 | 226 | 7 | 1 | 49/51/53 | 10000/15000/30000 | 40/30 | 0 | B 3-8; L 4-11 | Tempest (ServerLibrary/Models/Magics/Wizard/Tempest.cs) |
| 229 | JudgementOfHeaven | PLAYABLE | 51 | 264 | 6 | 1 | 52/57/62 | 20000/30000/50000 | 40/30 | 0 | B 0-0; L 0-0 | JudgementOfHeaven (ServerLibrary/Models/Magics/Wizard/JudgementOfHeaven.cs) |
| 230 | ThunderStrike | PLAYABLE | 52 | 266 | 6 | 1 | 54/59/64 | 15000/20000/30000 | 30/70 | 0 | B 14-18; L 14-18 | ThunderStrike (ServerLibrary/Models/Magics/Wizard/ThunderStrike.cs) |
| 231 | FireBounce | PLAYABLE | 53 | 0 | 0 | 1 | 15/17/19 | 400/500/600 | 6/6 | 0 | B 7-11; L 15-19 | FireBounce (ServerLibrary/Models/Magics/Wizard/FireBounce.cs) |
| 232 | ElementalHurricane | PLAYABLE | 54 | 436 | 7 | 1 | 83/85/87 | 15000/30000/45000 | 20/35 | 0 | B 16-24; L 15-18 | ElementalHurricane (ServerLibrary/Models/Magics/Wizard/ElementalHurricane.cs) |
| 233 | SuperiorMagicShield | PLAYABLE | 55 | 444 | 10 | 1 | 65/70/75 | 2000/4000/6000 | 20/60 | 0 | B 0-0; L 0-0 | SuperiorMagicShield (ServerLibrary/Models/Magics/Wizard/SuperiorMagicShield.cs) |
| 234 | Burning | PLAYABLE | 56 | 484 | 4 | 3 | 76/80/86 | 40000/60000/80000 | 20/120 | 0 | B 12-18; L 12-16 | Burning (ServerLibrary/Models/Magics/Wizard/Burning.cs) |
| 235 | Shocked | PLAYABLE | 57 | 532 | 6 | 3 | 85/88/91 | 450/1000/1650 | 20/45 | 0 | B 20-30; L 18-24 | Shocked (ServerLibrary/Models/Magics/Wizard/Shocked.cs) |
| 236 | LightningStrike | PLAYABLE | 58 | 452 | 6 | 1 | 90/90/90 | 10000/20000/30000 | 50/45 | 0 | B 16-22; L 10-14 | LightningStrike (ServerLibrary/Models/Magics/Wizard/LightningStrike.cs) |
| 237 | MirrorImage | PLAYABLE | 131 | 252 | 0 | 1 | 56/61/66 | 10000/18000/32000 | 10/10 | 0 | B 0-0; L 0-0 | MirrorImage (ServerLibrary/Models/Magics/Wizard/MirrorImage.cs) |
| 238 | IceRain | PLAYABLE | 137 | 486 | 5 | 1 | 82/86/90 | 50000/100000/150000 | 50/50 | 0 | B 5-10; L 2-4 | IceRain (ServerLibrary/Models/Magics/Wizard/IceRain.cs) |
| 239 | FrostBite | PLAYABLE | 139 | 390 | 5 | 1 | 58/60/62 | 2500/5000/9000 | 100/100 | 25000 | B 50-50; L 75-75 | FrostBite (ServerLibrary/Models/Magics/Wizard/FrostBite.cs) |
| 240 | Asteroid | PLAYABLE | 144 | 392 | 4 | 1 | 80/82/84 | 7500/15000/22500 | 200/200 | 3300 | B 50-80; L 70-120 | Asteroid (ServerLibrary/Models/Magics/Wizard/Asteroid.cs) |
| 241 | Storm | NOT CODED | 157 | 492 | 0 | 1 | 86/88/91 | 20000/30500/41000 | 0/0 | 0 | B 0-0; L 0-0 | Storm (ServerLibrary/Models/Magics/Wizard/Storm.cs) |
| 242 | Tornado | NOT CODED | 158 | 508 | 7 | 1 | 95/96/97 | 15000/30000/45000 | 0/0 | 0 | B 0-0; L 0-0 | Tornado (ServerLibrary/Models/Magics/Wizard/Tornado.cs) |
| 243 | IceAura | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | IceAura (ServerLibrary/Models/Magics/Wizard/IceAura.cs) |
| 244 | IceDragon | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | IceDragon (ServerLibrary/Models/Magics/Wizard/IceDragon.cs) |
| 245 | IceBreaker | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | IceBreaker (ServerLibrary/Models/Magics/Wizard/IceBreaker.cs) |
| 246 | FrozenDragon | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | FrozenDragon (ServerLibrary/Models/Magics/Wizard/FrozenDragon.cs) |
| 247 | UnityWithNature | NOT CODED | — | — | — | — | — | — | — | — | — | — |

## TAOIST

Enum **52** · DB **47** · handlers **51** · jugables **47** · enum-only **0** · DB sin handler **0** · handler sin DB **4** · NOT CODED **1** · UNUSED **0**.

| MagicType | Nombre | Estado | DB idx | Icon | School | Property | Need L1/L2/L3 | Exp 1/2/3 | Base/Level Cost | Delay | Powers | Handler |
|---:|---|---|---:|---:|---:|---:|---|---|---|---:|---|---|
| 300 | Heal | PLAYABLE | 59 | 2 | 8 | 1 | 7/9/11 | 100/200/300 | 2/7 | 0 | B 0-0; L 11-15 | Heal (ServerLibrary/Models/Magics/Taoist/Heal.cs) |
| 301 | SpiritSword | PLAYABLE | 60 | 6 | 11 | 2 | 8/10/12 | 100/200/300 | 0/0 | 0 | B 0-0; L 9-9 | SpiritSword (ServerLibrary/Models/Magics/Taoist/SpiritSword.cs) |
| 302 | PoisonDust | PLAYABLE | 61 | 10 | 9 | 1 | 12/14/16 | 200/300/400 | 5/10 | 0 | B 15-25; L 25-55 | PoisonDust (ServerLibrary/Models/Magics/Taoist/PoisonDust.cs) |
| 303 | ExplosiveTalisman | PLAYABLE | 62 | 24 | 9 | 1 | 13/15/17 | 200/300/400 | 3/6 | 0 | B 3-3; L 6-10 | ExplosiveTalisman (ServerLibrary/Models/Magics/Taoist/ExplosiveTalisman.cs) |
| 304 | EvilSlayer | PLAYABLE | 63 | 72 | 8 | 1 | 14/16/18 | 300/400/500 | 3/6 | 0 | B 3-3; L 6-10 | EvilSlayer (ServerLibrary/Models/Magics/Taoist/EvilSlayer.cs) |
| 305 | Invisibility | PLAYABLE | 64 | 34 | 9 | 1 | 20/22/24 | 500/600/700 | 5/5 | 0 | B 5-10; L 5-15 | Invisibility (ServerLibrary/Models/Magics/Taoist/Invisibility.cs) |
| 306 | MagicResistance | PLAYABLE | 65 | 26 | 9 | 1 | 21/23/25 | 500/600/700 | 5/10 | 0 | B 30-50; L 40-120 | MagicResistance (ServerLibrary/Models/Magics/Taoist/MagicResistance.cs) |
| 307 | MassInvisibility | PLAYABLE | 66 | 36 | 9 | 1 | 23/25/27 | 600/700/800 | 5/10 | 0 | B 5-10; L 5-15 | MassInvisibility (ServerLibrary/Models/Magics/Taoist/MassInvisibility.cs) |
| 308 | GreaterEvilSlayer | PLAYABLE | 67 | 74 | 8 | 1 | 24/26/28 | 600/700/800 | 4/8 | 0 | B 7-7; L 8-14 | GreaterEvilSlayer (ServerLibrary/Models/Magics/Taoist/GreaterEvilSlayer.cs) |
| 309 | Resilience | PLAYABLE | 68 | 28 | 9 | 1 | 25/27/29 | 700/800/900 | 5/10 | 0 | B 30-50; L 40-120 | Resilience (ServerLibrary/Models/Magics/Taoist/Resilience.cs) |
| 310 | TrapOctagon | PLAYABLE | 69 | 30 | 9 | 1 | 27/29/31 | 800/900/1000 | 10/15 | 0 | B 10-20; L 10-20 | TrapOctagon (ServerLibrary/Models/Magics/Taoist/TrapOctagon.cs) |
| 311 | CombatKick | PLAYABLE | 70 | 70 | 11 | 1 | 28/30/32 | 900/1000/1100 | 10/20 | 0 | B 2-3; L 3-3 | CombatKick (ServerLibrary/Models/Magics/Taoist/CombatKick.cs) |
| 312 | ElementalSuperiority | PLAYABLE | 71 | 176 | 9 | 1 | 29/31/33 | 900/1000/1100 | 5/10 | 0 | B 30-50; L 40-120 | ElementalSuperiority (ServerLibrary/Models/Magics/Taoist/ElementalSuperiority.cs) |
| 313 | MassHeal | PLAYABLE | 72 | 56 | 8 | 1 | 31/33/35 | 1000/1100/1200 | 20/10 | 0 | B 8-8; L 16-24 | MassHeal (ServerLibrary/Models/Magics/Taoist/MassHeal.cs) |
| 314 | BloodLust | PLAYABLE | 73 | 186 | 9 | 1 | 34/36/38 | 1000/1100/1200 | 5/10 | 0 | B 30-50; L 40-120 | BloodLust (ServerLibrary/Models/Magics/Taoist/BloodLust.cs) |
| 315 | Resurrection | PLAYABLE | 74 | 152 | 8 | 1 | 35/37/39 | 500/600/700 | 100/100 | 0 | B 10-20; L 15-30 | Resurrection (ServerLibrary/Models/Magics/Taoist/Resurrection.cs) |
| 316 | Purification | PLAYABLE | 75 | 238 | 8 | 1 | 38/41/44 | 1000/1500/3000 | 10/20 | 0 | B 10-20; L 15-30 | Purification (ServerLibrary/Models/Magics/Taoist/Purification.cs) |
| 317 | Transparency | PLAYABLE | 76 | 240 | 9 | 1 | 43/45/47 | 5000/7500/15000 | 80/120 | 5000 | B 5-10; L 5-15 | Transparency (ServerLibrary/Models/Magics/Taoist/Transparency.cs) |
| 318 | CelestialLight | PLAYABLE | 77 | 242 | 8 | 1 | 46/48/50 | 8000/12000/24000 | 50/60 | 0 | B 30-30; L 30-30 | CelestialLight (ServerLibrary/Models/Magics/Taoist/CelestialLight.cs) |
| 319 | EmpoweredHealing | PLAYABLE | 78 | 256 | 8 | 3 | 47/53/60 | 10000/18000/32000 | 2/7 | 0 | B 12-12; L 24-32 | EmpoweredHealing (ServerLibrary/Models/Magics/Taoist/EmpoweredHealing.cs) |
| 320 | LifeSteal | PLAYABLE | 79 | 270 | 8 | 1 | 48/55/62 | 10000/18000/32000 | 10/25 | 0 | B 30-30; L 60-60 | LifeSteal (ServerLibrary/Models/Magics/Taoist/LifeSteal.cs) |
| 321 | ImprovedExplosiveTalisman | PLAYABLE | 80 | 246 | 9 | 1 | 49/51/53 | 10000/15000/30000 | 10/18 | 0 | B 8-8; L 12-20 | ImprovedExplosiveTalisman (ServerLibrary/Models/Magics/Taoist/ImprovedExplosiveTalisman.cs) |
| 322 | AugmentPoisonDust | PLAYABLE | 81 | 268 | 9 | 3 | 50/54/58 | 30000/33000/36000 | 0/0 | 5000 | B 3-3; L 9-9 | GreaterPoisonDust (ServerLibrary/Models/Magics/Taoist/GreaterPoisonDust.cs) |
| 323 | CursedDoll | PLAYABLE | 82 | 272 | 10 | 1 | 52/56/61 | 10000/15000/25000 | 15/50 | 0 | B 10-10; L 20-20 | CursedDoll (ServerLibrary/Models/Magics/Taoist/CursedDoll.cs) |
| 324 | ThunderKick | PLAYABLE | 83 | 248 | 11 | 1 | 54/59/64 | 10000/18000/32000 | 10/20 | 0 | B 2-3; L 3-3 | ThunderKick (ServerLibrary/Models/Magics/Taoist/ThunderKick.cs) |
| 325 | SoulResonance | PLAYABLE | 84 | 482 | 8 | 1 | 84/84/84 | 0/0/0 | 55/60 | 0 | B 20-20; L 5-5 | SoulResonance (ServerLibrary/Models/Magics/Taoist/SoulResonance.cs) |
| 326 | Parasite | PLAYABLE | 85 | 396 | 9 | 1 | 62/66/70 | 7500/10000/13000 | 80/150 | 0 | B 2-2; L 1-1 | Parasite (ServerLibrary/Models/Magics/Taoist/Parasite.cs) |
| 327 | Spiritualism | PLAYABLE | 86 | 394 | 9 | 1 | 80/82/84 | 5500/7000/9000 | 15/5 | 0 | B 1-1; L 1-1 | Spiritualism (ServerLibrary/Models/Magics/Taoist/Spiritualism.cs) |
| 328 | AugmentExplosiveTalisman | PLAYABLE | 124 | 24 | 0 | 3 | 17/34/51 | 6000/12000/24000 | 0/0 | 3000 | B 1-1; L 3-3 | AugmentExplosiveTalisman (ServerLibrary/Models/Magics/Taoist/AugmentExplosiveTalisman.cs) |
| 329 | AugmentEvilSlayer | PLAYABLE | 125 | 72 | 0 | 3 | 17/34/51 | 6000/12000/24000 | 0/0 | 3000 | B 1-1; L 3-3 | AugmentEvilSlayer (ServerLibrary/Models/Magics/Taoist/AugmentEvilSlayer.cs) |
| 330 | AugmentPurification | PLAYABLE | 126 | 238 | 0 | 3 | 55/58/62 | 15000/20000/28000 | 0/0 | 10000 | B 1-1; L 3-3 | AugmentPurification (ServerLibrary/Models/Magics/Taoist/AugmentPurification.cs) |
| 331 | AugmentResurrection | PLAYABLE | 127 | 152 | 0 | 3 | 75/77/80 | 2500/5000/10000 | 0/0 | 60000 | B 1-1; L 3-3 | AugmentResurrection (ServerLibrary/Models/Magics/Taoist/AugmentResurrection.cs) |
| 332 | SummonSkeleton | PLAYABLE | 130 | 32 | 10 | 1 | 17/19/21 | 400/500/600 | 10/15 | 0 | B 0-0; L 0-0 | SummonSkeleton (ServerLibrary/Models/Magics/Taoist/SummonSkeleton.cs) |
| 333 | SummonShinsu | PLAYABLE | 133 | 58 | 10 | 1 | 30/32/34 | 900/1000/1100 | 15/15 | 0 | B 0-0; L 0-0 | SummonShinsu (ServerLibrary/Models/Magics/Taoist/SummonShinsu.cs) |
| 334 | SummonJinSkeleton | PLAYABLE | 132 | 208 | 10 | 1 | 33/35/37 | 1000/1100/1200 | 25/20 | 0 | B 0-0; L 0-0 | SummonJinSkeleton (ServerLibrary/Models/Magics/Taoist/SummonJinSkeleton.cs) |
| 335 | StrengthOfFaith | PLAYABLE | 129 | 244 | 10 | 1 | 40/42/44 | 2000/3000/6000 | 30/40 | 0 | B 60-60; L 180-180 | StrengthOfFaith (ServerLibrary/Models/Magics/Taoist/StrengthOfFaith.cs) |
| 336 | SummonDemonicCreature | PLAYABLE | 134 | 304 | 10 | 1 | 50/54/56 | 7000/9000/11000 | 20/30 | 0 | B 0-0; L 0-0 | SummonDemonicCreature (ServerLibrary/Models/Magics/Taoist/SummonDemonicCreature.cs) |
| 337 | DemonExplosion | PLAYABLE | 128 | 306 | 10 | 1 | 52/56/58 | 5500/6500/8500 | 100/80 | 10000 | B 25-25; L 25-25 | DemonExplosion (ServerLibrary/Models/Magics/Taoist/DemonExplosion.cs) |
| 338 | Infection | PLAYABLE | 140 | 446 | 9 | 3 | 65/70/75 | 7500/15000/30000 | 0/0 | 3000 | B 2-2; L 2-3 | Infection (ServerLibrary/Models/Magics/Taoist/Infection.cs) |
| 339 | DemonicRecovery | PLAYABLE | 143 | 536 | 10 | 1 | 48/51/54 | 9000/10000/11000 | 100/80 | 0 | B 25-25; L 75-75 | DemonicRecovery (ServerLibrary/Models/Magics/Taoist/DemonicRecovery.cs) |
| 340 | Neutralize | PLAYABLE | 148 | 480 | 9 | 1 | 80/86/91 | 20000/40000/60000 | 10/5 | 0 | B 0-0; L 0-0 | Neutralize (ServerLibrary/Models/Magics/Taoist/Neutralize.cs) |
| 341 | AugmentNeutralize | PLAYABLE | 149 | 480 | 0 | 3 | 80/86/91 | 4000/6000/8000 | 0/0 | 0 | B 1-1; L 1-1 | AugmentNeutralize (ServerLibrary/Models/Magics/Taoist/AugmentNeutralize.cs) |
| 342 | DarkSoulPrison | PLAYABLE | 150 | 454 | 9 | 1 | 90/90/90 | 10000/20000/30000 | 10/5 | 0 | B 12-15; L 1-2 | DarkSoulPrison (ServerLibrary/Models/Magics/Taoist/DarkSoulPrison.cs) |
| 343 | SearingLight | PLAYABLE | 151 | 438 | 8 | 1 | 83/85/87 | 7000/10000/16000 | 15/5 | 5000 | B 12-15; L 1-2 | SearingLight (ServerLibrary/Models/Magics/Taoist/SearingLight.cs) |
| 344 | AugmentCelestialLight | PLAYABLE | 159 | 462 | 8 | 3 | 82/83/84 | 4000/6000/12000 | 0/0 | 0 | B 0-0; L 0-0 | AugmentCelestialLight (ServerLibrary/Models/Magics/Taoist/AugmentCelestialLight.cs) |
| 345 | CorpseExploder | PLAYABLE | 160 | 490 | 9 | 1 | 86/88/95 | 30000/30000/30000 | 30/5 | 0 | B 15-30; L 5-10 | CorpseExploder (ServerLibrary/Models/Magics/Taoist/CorpseExploder.cs) |
| 346 | SummonDead | PLAYABLE | 161 | 514 | 10 | 1 | 95/96/97 | 10000/11000/12000 | 0/0 | 0 | B 0-0; L 0-0 | SummonDead (ServerLibrary/Models/Magics/Taoist/SummonDead.cs) |
| 347 | BindingTalisman | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | BindingTalisman (ServerLibrary/Models/Magics/Taoist/BindingTalisman.cs) |
| 348 | BrainStorm | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | BrainStorm (ServerLibrary/Models/Magics/Taoist/BrainStorm.cs) |
| 349 | HeavenlySky | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | HeavenlySky (ServerLibrary/Models/Magics/Taoist/HeavenlySky.cs) |
| 350 | PoisonCloud | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | PoisonCloud (ServerLibrary/Models/Magics/Taoist/PoisonCloud.cs) |
| 351 | SupremeHealing | NOT CODED | — | — | — | — | — | — | — | — | — | — |

## ASSASSIN

Enum **58** · DB **53** · handlers **56** · jugables **52** · enum-only **0** · DB sin handler **0** · handler sin DB **4** · NOT CODED **1** · UNUSED **1**.

| MagicType | Nombre | Estado | DB idx | Icon | School | Property | Need L1/L2/L3 | Exp 1/2/3 | Base/Level Cost | Delay | Powers | Handler |
|---:|---|---|---:|---:|---:|---:|---|---|---|---:|---|---|
| 401 | WillowDance | PLAYABLE | 87 | 308 | 12 | 2 | 7/9/11 | 100/200/300 | 0/0 | 0 | B 0-0; L 6-6 | WillowDance (ServerLibrary/Models/Magics/Assassin/WillowDance.cs) |
| 402 | VineTreeDance | PLAYABLE | 88 | 310 | 12 | 2 | 10/12/14 | 250/350/450 | 0/0 | 0 | B 0-0; L 9-9 | VineTreeDance (ServerLibrary/Models/Magics/Assassin/VineTreeDance.cs) |
| 403 | Discipline | PLAYABLE | 89 | 314 | 12 | 2 | 12/14/16 | 300/400/500 | 0/0 | 0 | B 0-0; L 12-12 | Discipline (ServerLibrary/Models/Magics/Assassin/Discipline.cs) |
| 404 | PoisonousCloud | PLAYABLE | 90 | 312 | 12 | 1 | 14/16/18 | 300/400/500 | 5/20 | 20000 | B 5-5; L 10-10 | PoisonousCloud (ServerLibrary/Models/Magics/Assassin/PoisonousCloud.cs) |
| 405 | FullBloom | PLAYABLE | 91 | 328 | 13 | 5 | 19/21/23 | 400/500/600 | 2/4 | 3000 | B 85-85; L 85-85 | FullBloom (ServerLibrary/Models/Magics/Assassin/FullBloom.cs) |
| 406 | Cloak | PLAYABLE | 92 | 324 | 14 | 1 | 20/22/24 | 200/300/400 | 50/20 | 0 | B 0-0; L 0-0 | Cloak (ServerLibrary/Models/Magics/Assassin/Cloak.cs) |
| 407 | WhiteLotus | PLAYABLE | 93 | 330 | 13 | 5 | 22/24/26 | 500/600/700 | 3/5 | 3000 | B 65-65; L 45-45 | WhiteLotus (ServerLibrary/Models/Magics/Assassin/WhiteLotus.cs) |
| 408 | CalamityOfFullMoon | PLAYABLE | 94 | 340 | 13 | 2 | 22/24/26 | 500/600/700 | 4/6 | 0 | B 15-15; L 15-15 | CalamityOfFullMoon (ServerLibrary/Models/Magics/Assassin/CalamityOfFullMoon.cs) |
| 409 | WraithGrip | PLAYABLE | 95 | 316 | 12 | 1 | 24/26/28 | 300/400/500 | 10/24 | 60000 | B 4-4; L 3-3 | WraithGrip (ServerLibrary/Models/Magics/Assassin/WraithGrip.cs) |
| 410 | RedLotus | PLAYABLE | 96 | 332 | 13 | 5 | 24/26/28 | 600/700/800 | 4/6 | 3000 | B 70-70; L 50-50 | RedLotus (ServerLibrary/Models/Magics/Assassin/RedLotus.cs) |
| 411 | HellFire | PLAYABLE | 97 | 318 | 13 | 1 | 26/28/30 | 400/500/600 | 10/10 | 20000 | B 5-5; L 5-5 | HellFire (ServerLibrary/Models/Magics/Assassin/HellFire.cs) |
| 412 | PledgeOfBlood | PLAYABLE | 98 | 352 | 14 | 2 | 26/28/30 | 150/300/450 | 0/0 | 0 | B 0-0; L 7-7 | PledgeOfBlood (ServerLibrary/Models/Magics/Assassin/PledgeOfBlood.cs) |
| 413 | Rake | PLAYABLE | 99 | 376 | 14 | 1 | 26/28/30 | 2000/2200/2400 | 5/10 | 5000 | B 50-50; L 50-50 | Rake (ServerLibrary/Models/Magics/Assassin/Rake.cs) |
| 414 | SweetBrier | PLAYABLE | 100 | 334 | 13 | 5 | 27/29/31 | 700/800/900 | 5/7 | 3000 | B 75-75; L 65-65 | SweetBrier (ServerLibrary/Models/Magics/Assassin/SweetBrier.cs) |
| 415 | SummonPuppet | PLAYABLE | 101 | 326 | 14 | 1 | 30/32/34 | 400/500/600 | 10/30 | 30000 | B 60-60; L 40-40 | SummonPuppet (ServerLibrary/Models/Magics/Assassin/SummonPuppet.cs) |
| 416 | Karma | PLAYABLE | 102 | 342 | 14 | 5 | 30/35/40 | 200/400/800 | 0/0 | 15000 | B 10-10; L 15-20 | Karma (ServerLibrary/Models/Magics/Assassin/Karma.cs) |
| 417 | TouchOfTheDeparted | PLAYABLE | 103 | 354 | 12 | 3 | 30/32/34 | 150/300/450 | 0/10 | 0 | B 0-0; L 0-0 | TouchOfTheDeparted (ServerLibrary/Models/Magics/Assassin/TouchOfTheDeparted.cs) |
| 418 | WaningMoon | PLAYABLE | 104 | 350 | 14 | 2 | 32/34/36 | 500/600/700 | 4/12 | 0 | B 20-20; L 20-20 | WaningMoon (ServerLibrary/Models/Magics/Assassin/WaningMoon.cs) |
| 419 | GhostWalk | PLAYABLE | 105 | 356 | 14 | 3 | 32/34/36 | 150/300/450 | 0/16 | 0 | B 0-0; L 0-0 | GhostWalk (ServerLibrary/Models/Magics/Assassin/GhostWalk.cs) |
| 420 | ElementalPuppet | PLAYABLE | 106 | 358 | 14 | 3 | 34/36/38 | 1000/2000/3000 | 0/0 | 0 | B 0-0; L 0-0 | ElementalPuppet (ServerLibrary/Models/Magics/Assassin/ElementalPuppet.cs) |
| 421 | Rejuvenation | PLAYABLE | 107 | 336 | 12 | 2 | 35/37/39 | 1000/1100/1200 | 6/2 | 0 | B 0-0; L 0-0 | Rejuvenation (ServerLibrary/Models/Magics/Assassin/Rejuvenation.cs) |
| 422 | Resolution | PLAYABLE | 108 | 344 | 14 | 3 | 35/37/39 | 200/250/300 | 2/4 | 0 | B 5-5; L 5-5 | Resolution (ServerLibrary/Models/Magics/Assassin/Resolution.cs) |
| 423 | ChangeOfSeasons | PLAYABLE | 109 | 360 | 0 | 0 | 36/0/0 | 0/0/0 | 0/0 | 0 | B 0-0; L 0-0 | ChangeOfSeasons (ServerLibrary/Models/Magics/Assassin/ChangeOfSeasons.cs) |
| 424 | Release | PLAYABLE | 110 | 378 | 14 | 2 | 36/38/40 | 1200/1500/1800 | 1/4 | 0 | B 0-0; L 40-80 | Release (ServerLibrary/Models/Magics/Assassin/Release.cs) |
| 425 | FlameSplash | PLAYABLE | 111 | 320 | 13 | 4 | 38/40/42 | 1000/1100/1200 | 0/6 | 0 | B 30-30; L 100-100 | FlameSplash (ServerLibrary/Models/Magics/Assassin/FlameSplash.cs) |
| 426 | BloodyFlower | PLAYABLE | 112 | 374 | 13 | 5 | 12/22/33 | 2800/3200/3600 | 0/0 | 0 | B 5-5; L 10-10 | BloodyFlower (ServerLibrary/Models/Magics/Assassin/BloodyFlower.cs) |
| 427 | TheNewBeginning | PLAYABLE | 113 | 346 | 12 | 1 | 40/43/46 | 200/250/300 | 0/80 | 1000 | B 20-20; L 30-30 | TheNewBeginning (ServerLibrary/Models/Magics/Assassin/TheNewBeginning.cs) |
| 428 | DanceOfSwallow | PLAYABLE | 114 | 362 | 13 | 1 | 40/42/44 | 750/1050/1350 | 0/10 | 5000 | B 1-1; L 3-3 | DanceOfSwallow (ServerLibrary/Models/Magics/Assassin/DanceOfSwallow.cs) |
| 429 | DarkConversion | PLAYABLE | 115 | 364 | 12 | 1 | 42/44/46 | 1100/2200/3300 | 0/2 | 0 | B 2-2; L 8-8 | DarkConversion (ServerLibrary/Models/Magics/Assassin/DarkConversion.cs) |
| 430 | DragonRepulse | PLAYABLE | 116 | 322 | 12 | 1 | 45/47/49 | 6000/9000/18000 | 100/100 | 30000 | B 50-50; L 50-50 | DragonRepulse (ServerLibrary/Models/Magics/Assassin/DragonRepulse.cs) |
| 431 | AdventOfDemon | PLAYABLE | 117 | 338 | 13 | 2 | 45/47/49 | 6000/9000/18000 | 4/2 | 0 | B 3-3; L 7-7 | AdventOfDemon (ServerLibrary/Models/Magics/Assassin/AdventOfDemon.cs) |
| 432 | AdventOfDevil | PLAYABLE | 118 | 348 | 14 | 2 | 45/47/49 | 6000/9000/18000 | 3/2 | 0 | B 3-3; L 7-7 | AdventOfDevil (ServerLibrary/Models/Magics/Assassin/AdventOfDevil.cs) |
| 433 | Abyss | PLAYABLE | 119 | 366 | 12 | 1 | 45/47/49 | 2500/3000/3500 | 1/20 | 10000 | B 0-0; L 0-0 | Abyss (ServerLibrary/Models/Magics/Assassin/Abyss.cs) |
| 434 | FlashOfLight | PLAYABLE | 120 | 368 | 13 | 1 | 45/47/50 | 3000/3300/3600 | 22/72 | 5000 | B 180-180; L 180-180 | FlashOfLight (ServerLibrary/Models/Magics/Assassin/FlashOfLight.cs) |
| 435 | Stealth | PLAYABLE | 121 | 380 | 14 | 3 | 45/47/49 | 1600/2000/2400 | 0/0 | 0 | B 10-10; L 15-15 | Stealth (ServerLibrary/Models/Magics/Assassin/Stealth.cs) |
| 436 | Evasion | PLAYABLE | 122 | 370 | 12 | 1 | 47/49/51 | 1400/2100/2800 | 20/20 | 0 | B 45-45; L 45-45 | Evasion (ServerLibrary/Models/Magics/Assassin/Evasion.cs) |
| 437 | RagingWind | PLAYABLE | 123 | 372 | 12 | 1 | 47/49/51 | 2400/2800/3200 | 20/20 | 0 | B 45-45; L 45-45 | RagingWind (ServerLibrary/Models/Magics/Assassin/RagingWind.cs) |
| 438 | Unused | UNUSED | 136 | 0 | 0 | 0 | 0/0/0 | 0/0/0 | 0/0 | 0 | B 0-0; L 0-0 | — |
| 439 | Massacre | PLAYABLE | 141 | 382 | 0 | 2 | 65/70/75 | 10000/20000/40000 | 0/0 | 0 | B 5-5; L 5-5 | Massacre (ServerLibrary/Models/Magics/Assassin/Massacre.cs) |
| 440 | ArtOfShadows | PLAYABLE | 145 | 396 | 0 | 2 | 75/79/82 | 10000/20000/40000 | 0/0 | 0 | B 2-3; L 4-6 | ArtOfShadows (ServerLibrary/Models/Magics/Assassin/ArtOfShadows.cs) |
| 441 | DragonBlood | PLAYABLE | 162 | 382 | 13 | 2 | 60/62/64 | 3000/3200/3400 | 0/0 | 0 | B 5-5; L 5-5 | DragonBlood (ServerLibrary/Models/Magics/Assassin/DragonBlood.cs) |
| 442 | FatalBlow | PLAYABLE | 163 | 474 | 13 | 2 | 60/70/80 | 3000/6000/8000 | 0/0 | 0 | B 5-5; L 5-5 | FatalBlow (ServerLibrary/Models/Magics/Assassin/FatalBlow.cs) |
| 443 | LastStand | PLAYABLE | 164 | 448 | 12 | 2 | 65/75/85 | 500/600/800 | 0/0 | 0 | B 5-5; L 5-5 | LastStand (ServerLibrary/Models/Magics/Assassin/LastStand.cs) |
| 444 | MagicCombustion | PLAYABLE | 165 | 478 | 12 | 1 | 70/72/76 | 15000/25000/33000 | 10/10 | 10000 | B 5-5; L 5-5 | MagicCombustion (ServerLibrary/Models/Magics/Assassin/MagicCombustion.cs) |
| 445 | Vitality | PLAYABLE | 166 | 472 | 12 | 2 | 70/74/80 | 2000/3000/6000 | 0/0 | 0 | B 5-5; L 5-5 | Vitality (ServerLibrary/Models/Magics/Assassin/Vitality.cs) |
| 446 | Chain | PLAYABLE | 167 | 476 | 12 | 1 | 75/80/84 | 20000/35000/40000 | 15/15 | 15000 | B 20-20; L 20-20 | Chain (ServerLibrary/Models/Magics/Assassin/Chain.cs) |
| 447 | Concentration | PLAYABLE | 168 | 384 | 12 | 1 | 80/82/84 | 5000/5500/6000 | 30/30 | 0 | B 60-60; L 60-60 | Concentration (ServerLibrary/Models/Magics/Assassin/Concentration.cs) |
| 448 | DualWeaponSkills | PLAYABLE | 169 | 464 | 12 | 2 | 82/83/84 | 35000/38000/41000 | 0/0 | 0 | B 5-5; L 5-5 | DualWeaponSkills (ServerLibrary/Models/Magics/Assassin/DualWeaponSkills.cs) |
| 449 | Containment | PLAYABLE | 170 | 440 | 12 | 1 | 83/85/87 | 12000/18000/36000 | 0/0 | 5000 | B 0-0; L 0-0 | Containment (ServerLibrary/Models/Magics/Assassin/Containment.cs) |
| 450 | DragonWave | PLAYABLE | 171 | 542 | 13 | 3 | 85/90/95 | 50000/55000/60000 | 1/1 | 0 | B 0-0; L 0-0 | DragonWave (ServerLibrary/Models/Magics/Assassin/DragonWave.cs) |
| 451 | Hemorrhage | PLAYABLE | 172 | 494 | 13 | 1 | 86/88/91 | 40000/42000/46000 | 25/25 | 5000 | B 5-5; L 5-5 | Hemorrhage (ServerLibrary/Models/Magics/Assassin/Hemorrhage.cs) |
| 452 | BurningFire | PLAYABLE | 173 | 456 | 13 | 1 | 90/90/90 | 10000/20000/30000 | 30/30 | 5000 | B 15-15; L 15-15 | BurningFire (ServerLibrary/Models/Magics/Assassin/BurningFire.cs) |
| 453 | ChainOfFire | PLAYABLE | 174 | 520 | 12 | 3 | 95/96/97 | 20000/35000/40000 | 0/0 | 0 | B 100-100; L 100-100 | ChainOfFire (ServerLibrary/Models/Magics/Assassin/ChainOfFire.cs) |
| 454 | FlamingDaggers | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | FlamingDaggers (ServerLibrary/Models/Magics/Assassin/FlamingDaggers.cs) |
| 455 | Shredding | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | Shredding (ServerLibrary/Models/Magics/Assassin/Shredding.cs) |
| 456 | FourWheels | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | FourWheels (ServerLibrary/Models/Magics/Assassin/FourWheels.cs) |
| 457 | CrescentMoon | HANDLER / NO DB | — | — | — | — | — | — | — | — | — | CrescentMoon (ServerLibrary/Models/Magics/Assassin/CrescentMoon.cs) |
| 458 | ManaBurn | NOT CODED | — | — | — | — | — | — | — | — | — | — |

## Integridad de registro

- Handlers registrados fuera del catálogo activo de cuatro clases: **0**.
- Clases anotadas que no pasan la regla de registro de `SEnvir.CreateMagic`: **0**.
- Errores de consistencia del auditor: **0**.

El JSON generado junto a este informe conserva todos los campos reales de `MagicInfo`, incluido `Description`, y la ruta/clase exacta del handler cuando existe.
