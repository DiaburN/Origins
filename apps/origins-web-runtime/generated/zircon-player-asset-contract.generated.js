// GENERATED from pinned Suprcode/Zircon. Do not edit by hand.
export const ZIRCON_PLAYER_ASSET_CONTRACT = Object.freeze({
  "schema": "origins.zircon.web-player-assets.v1",
  "zirconCommit": "cbf1aa919083bc13fc3f23f93772a8ab8370632d",
  "sourceHashes": {
    "Enum.cs": "33F7A73C35AD29CA4592FFE11E51ABF4910D27DBCA7C701149C55A9CFE902997",
    "FrameSet.cs": "CFA9B931A16394CB8C5EFA291A7AAC4ACB4F12B0F05641369E37DD02CEE26CC4",
    "Libraries.cs": "61DC70418C07736761E2ED81226ECD82448ABCE5FE2BDEE4EAD011D7793046C7",
    "PlayerObject.cs": "5D0900412682F432FA4B3DC555C998CAE4AA4D2C2CB72D9176829CF5E31BAADB",
    "MapObject.cs": "3982B5515E80E6EC54F21F40B47DDD34636EAE45A637EB97924F7803E11632A0",
    "Functions.cs": "97BFEBAB68B178AFA4809D83C11621C52A577A4980221984AFE5F8D857F0C581"
  },
  "mirAnimation": {
    "Standing": 0,
    "Walking": 1,
    "CreepStanding": 2,
    "CreepWalkSlow": 3,
    "CreepWalkFast": 4,
    "Running": 5,
    "Pushed": 6,
    "Combat1": 7,
    "Combat2": 8,
    "Combat3": 9,
    "Combat4": 10,
    "Combat5": 11,
    "Combat6": 12,
    "Combat7": 13,
    "Combat8": 14,
    "Combat9": 15,
    "Combat10": 16,
    "Combat11": 17,
    "Combat12": 18,
    "Combat13": 19,
    "Combat14": 20,
    "Combat15": 21,
    "Harvest": 22,
    "Stance": 23,
    "Struck": 24,
    "Die": 25,
    "Dead": 26,
    "Skeleton": 27,
    "Show": 28,
    "Hide": 29,
    "HorseStanding": 30,
    "HorseWalking": 31,
    "HorseRunning": 32,
    "HorseStruck": 33,
    "StoneStanding": 34,
    "DragonRepulseStart": 35,
    "DragonRepulseMiddle": 36,
    "DragonRepulseEnd": 37,
    "ChannellingStart": 38,
    "ChannellingMiddle": 39,
    "ChannellingEnd": 40,
    "FishingCast": 41,
    "FishingWait": 42,
    "FishingReel": 43,
    "TamingCast": 44,
    "TamingWait": 45
  },
  "playerFrames": {
    "Standing": {
      "startIndex": 0,
      "frameCount": 4,
      "offset": 10,
      "delaysMs": [
        500,
        500,
        500,
        500
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Walking": {
      "startIndex": 80,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Running": {
      "startIndex": 160,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "CreepStanding": {
      "startIndex": 1680,
      "frameCount": 4,
      "offset": 10,
      "delaysMs": [
        500,
        500,
        500,
        500
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "CreepWalkFast": {
      "startIndex": 1760,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "CreepWalkSlow": {
      "startIndex": 1760,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        200,
        200,
        200,
        200,
        200,
        200
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Pushed": {
      "startIndex": 240,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        50,
        50,
        50,
        50,
        50,
        50
      ],
      "reversed": true,
      "staticSpeed": true
    },
    "Stance": {
      "startIndex": 400,
      "frameCount": 3,
      "offset": 10,
      "delaysMs": [
        500,
        500,
        500
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Harvest": {
      "startIndex": 480,
      "frameCount": 2,
      "offset": 10,
      "delaysMs": [
        300,
        300
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat1": {
      "startIndex": 560,
      "frameCount": 5,
      "offset": 10,
      "delaysMs": [
        100,
        200,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat2": {
      "startIndex": 640,
      "frameCount": 5,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        200,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat3": {
      "startIndex": 720,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat4": {
      "startIndex": 800,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat5": {
      "startIndex": 880,
      "frameCount": 10,
      "offset": 10,
      "delaysMs": [
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat6": {
      "startIndex": 960,
      "frameCount": 10,
      "offset": 10,
      "delaysMs": [
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat7": {
      "startIndex": 1040,
      "frameCount": 10,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat8": {
      "startIndex": 1120,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        50,
        50,
        50,
        50,
        50,
        50
      ],
      "reversed": false,
      "staticSpeed": true
    },
    "Combat9": {
      "startIndex": 1200,
      "frameCount": 10,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat10": {
      "startIndex": 1280,
      "frameCount": 10,
      "offset": 10,
      "delaysMs": [
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat11": {
      "startIndex": 1360,
      "frameCount": 10,
      "offset": 10,
      "delaysMs": [
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat12": {
      "startIndex": 1440,
      "frameCount": 10,
      "offset": 10,
      "delaysMs": [
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60,
        60
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat13": {
      "startIndex": 1520,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat14": {
      "startIndex": 1600,
      "frameCount": 8,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Combat15": {
      "startIndex": 400,
      "frameCount": 3,
      "offset": 10,
      "delaysMs": [
        200,
        200,
        200
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "DragonRepulseStart": {
      "startIndex": 1600,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "DragonRepulseMiddle": {
      "startIndex": 1605,
      "frameCount": 1,
      "offset": 10,
      "delaysMs": [
        1000
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "DragonRepulseEnd": {
      "startIndex": 1606,
      "frameCount": 2,
      "offset": 10,
      "delaysMs": [
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Struck": {
      "startIndex": 1840,
      "frameCount": 3,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Die": {
      "startIndex": 1920,
      "frameCount": 10,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "Dead": {
      "startIndex": 1929,
      "frameCount": 1,
      "offset": 10,
      "delaysMs": [
        1000
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "FishingCast": {
      "startIndex": 2000,
      "frameCount": 8,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "FishingWait": {
      "startIndex": 2080,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        120,
        120,
        120,
        120,
        120,
        120
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "FishingReel": {
      "startIndex": 2160,
      "frameCount": 8,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "HorseStanding": {
      "startIndex": 2240,
      "frameCount": 4,
      "offset": 10,
      "delaysMs": [
        500,
        500,
        500,
        500
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "HorseWalking": {
      "startIndex": 2320,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "HorseRunning": {
      "startIndex": 2400,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "HorseStruck": {
      "startIndex": 2480,
      "frameCount": 3,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "ChannellingStart": {
      "startIndex": 560,
      "frameCount": 4,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "ChannellingMiddle": {
      "startIndex": 563,
      "frameCount": 1,
      "offset": 10,
      "delaysMs": [
        1000
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "ChannellingEnd": {
      "startIndex": 0,
      "frameCount": 1,
      "offset": 10,
      "delaysMs": [
        60
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "TamingCast": {
      "startIndex": 720,
      "frameCount": 6,
      "offset": 10,
      "delaysMs": [
        100,
        100,
        100,
        100,
        100,
        100
      ],
      "reversed": false,
      "staticSpeed": false
    },
    "TamingWait": {
      "startIndex": 725,
      "frameCount": 1,
      "offset": 10,
      "delaysMs": [
        100
      ],
      "reversed": false,
      "staticSpeed": false
    }
  },
  "magicAnimationMap": {
    "Beckon": "Combat1",
    "MassBeckon": "Combat1",
    "FireBall": "Combat1",
    "IceBolt": "Combat1",
    "LightningBall": "Combat1",
    "GustBlast": "Combat1",
    "ScortchedEarth": "Combat1",
    "LightningBeam": "Combat1",
    "AdamantineFireBall": "Combat1",
    "FireBounce": "Combat1",
    "IceBlades": "Combat1",
    "FrozenEarth": "Combat1",
    "MeteorShower": "Combat1",
    "LightningStrike": "Combat1",
    "IceAura": "Combat1",
    "IceDragon": "Combat1",
    "ExplosiveTalisman": "Combat1",
    "EvilSlayer": "Combat1",
    "MagicResistance": "Combat1",
    "Resilience": "Combat1",
    "MassInvisibility": "Combat1",
    "GreaterEvilSlayer": "Combat1",
    "GreaterFrozenEarth": "Combat1",
    "Parasite": "Combat1",
    "ElementalSuperiority": "Combat1",
    "BloodLust": "Combat1",
    "LifeSteal": "Combat1",
    "ImprovedExplosiveTalisman": "Combat1",
    "Neutralize": "Combat1",
    "CorpseExploder": "Combat1",
    "SoulResonance": "Combat1",
    "SearingLight": "Combat1",
    "BindingTalisman": "Combat1",
    "BrainStorm": "Combat1",
    "Hemorrhage": "Combat1",
    "FlamingDaggers": "Combat1",
    "Shredding": "Combat1",
    "Interchange": "Combat2",
    "ElementalSwords": "Combat2",
    "TaecheonSword": "Combat2",
    "FireSword": "Combat2",
    "Repulsion": "Combat2",
    "ElectricShock": "Combat2",
    "LightningWave": "Combat2",
    "Cyclone": "Combat2",
    "Teleportation": "Combat2",
    "FireWall": "Combat2",
    "FireStorm": "Combat2",
    "BlowEarth": "Combat2",
    "ExpelUndead": "Combat2",
    "MagicShield": "Combat2",
    "IceStorm": "Combat2",
    "DragonTornado": "Combat2",
    "ChainLightning": "Combat2",
    "GeoManipulation": "Combat2",
    "Transparency": "Combat2",
    "ThunderBolt": "Combat2",
    "Renounce": "Combat2",
    "FrostBite": "Combat2",
    "Tempest": "Combat2",
    "JudgementOfHeaven": "Combat2",
    "ThunderStrike": "Combat2",
    "MirrorImage": "Combat2",
    "Asteroid": "Combat2",
    "SuperiorMagicShield": "Combat2",
    "IceRain": "Combat2",
    "Tornado": "Combat2",
    "IceBreaker": "Combat2",
    "FrozenDragon": "Combat2",
    "Heal": "Combat2",
    "PoisonDust": "Combat2",
    "Invisibility": "Combat2",
    "TrapOctagon": "Combat2",
    "MassHeal": "Combat2",
    "Resurrection": "Combat2",
    "Purification": "Combat2",
    "SummonSkeleton": "Combat2",
    "SummonJinSkeleton": "Combat2",
    "SummonShinsu": "Combat2",
    "StrengthOfFaith": "Combat2",
    "CelestialLight": "Combat2",
    "AugmentPoisonDust": "Combat2",
    "SummonDemonicCreature": "Combat2",
    "DemonExplosion": "Combat2",
    "CursedDoll": "Combat2",
    "DarkSoulPrison": "Combat2",
    "SummonDead": "Combat2",
    "HeavenlySky": "Combat2",
    "PoisonCloud": "Combat2",
    "ElementalHurricane": "ChannellingStart",
    "PoisonousCloud": "Combat14",
    "SummonPuppet": "Combat14",
    "Containment": "Combat14",
    "FourWheels": "Combat14",
    "CrescentMoon": "Combat14",
    "DragonRepulse": "DragonRepulseStart",
    "ThunderKick": "Combat7",
    "CombatKick": "Combat7",
    "HundredFist": "Combat8",
    "Cloak": "Combat9",
    "WraithGrip": "Combat9",
    "HellFire": "Combat9",
    "TheNewBeginning": "Combat9",
    "DarkConversion": "Combat9",
    "Abyss": "Combat9",
    "Evasion": "Combat9",
    "RagingWind": "Combat9",
    "Concentration": "Combat9",
    "BurningFire": "Combat9",
    "Chain": "Combat9",
    "Rake": "Combat5",
    "MagicCombustion": "Combat5",
    "FlashOfLight": "Combat10",
    "Defiance": "Combat15",
    "Might": "Combat15",
    "ReflectDamage": "Combat15",
    "Fetter": "Combat15",
    "Endurance": "Combat15",
    "Invincibility": "Combat15",
    "Spiritualism": "Combat15",
    "Shuriken": "Combat3",
    "SwiftBlade": "Combat3",
    "SeismicSlam": "Combat3",
    "CrushingWave": "Combat3"
  },
  "playerLibraries": [
    {
      "libraryFile": "M_Hum",
      "sourcePath": "Data/M-Hum.Zl",
      "fileName": "M-Hum.Zl"
    },
    {
      "libraryFile": "M_HumEx1",
      "sourcePath": "Data/M-HumEx1.Zl",
      "fileName": "M-HumEx1.Zl"
    },
    {
      "libraryFile": "M_HumEx2",
      "sourcePath": "Data/M-HumEx2.Zl",
      "fileName": "M-HumEx2.Zl"
    },
    {
      "libraryFile": "M_HumEx3",
      "sourcePath": "Data/M-HumEx3.Zl",
      "fileName": "M-HumEx3.Zl"
    },
    {
      "libraryFile": "M_HumEx4",
      "sourcePath": "Data/M-HumEx4.Zl",
      "fileName": "M-HumEx4.Zl"
    },
    {
      "libraryFile": "M_HumEx10",
      "sourcePath": "Data/M-HumEx10.Zl",
      "fileName": "M-HumEx10.Zl"
    },
    {
      "libraryFile": "M_HumEx11",
      "sourcePath": "Data/M-HumEx11.Zl",
      "fileName": "M-HumEx11.Zl"
    },
    {
      "libraryFile": "M_HumEx12",
      "sourcePath": "Data/M-HumEx12.Zl",
      "fileName": "M-HumEx12.Zl"
    },
    {
      "libraryFile": "M_HumEx13",
      "sourcePath": "Data/M-HumEx13.Zl",
      "fileName": "M-HumEx13.Zl"
    },
    {
      "libraryFile": "WM_Hum",
      "sourcePath": "Data/WM-Hum.Zl",
      "fileName": "WM-Hum.Zl"
    },
    {
      "libraryFile": "WM_HumEx1",
      "sourcePath": "Data/WM-HumEx1.Zl",
      "fileName": "WM-HumEx1.Zl"
    },
    {
      "libraryFile": "WM_HumEx2",
      "sourcePath": "Data/WM-HumEx2.Zl",
      "fileName": "WM-HumEx2.Zl"
    },
    {
      "libraryFile": "WM_HumEx3",
      "sourcePath": "Data/WM-HumEx3.Zl",
      "fileName": "WM-HumEx3.Zl"
    },
    {
      "libraryFile": "WM_HumEx4",
      "sourcePath": "Data/WM-HumEx4.Zl",
      "fileName": "WM-HumEx4.Zl"
    },
    {
      "libraryFile": "WM_HumEx10",
      "sourcePath": "Data/WM-HumEx10.Zl",
      "fileName": "WM-HumEx10.Zl"
    },
    {
      "libraryFile": "WM_HumEx11",
      "sourcePath": "Data/WM-HumEx11.Zl",
      "fileName": "WM-HumEx11.Zl"
    },
    {
      "libraryFile": "WM_HumEx12",
      "sourcePath": "Data/WM-HumEx12.Zl",
      "fileName": "WM-HumEx12.Zl"
    },
    {
      "libraryFile": "WM_HumEx13",
      "sourcePath": "Data/WM-HumEx13.Zl",
      "fileName": "WM-HumEx13.Zl"
    },
    {
      "libraryFile": "M_HumCx1",
      "sourcePath": "Data/M-HumCx1.Zl",
      "fileName": "M-HumCx1.Zl"
    },
    {
      "libraryFile": "WM_HumCx1",
      "sourcePath": "Data/WM-HumCx1.Zl",
      "fileName": "WM-HumCx1.Zl"
    },
    {
      "libraryFile": "M_Hair",
      "sourcePath": "Data/M-Hair.Zl",
      "fileName": "M-Hair.Zl"
    },
    {
      "libraryFile": "WM_Hair",
      "sourcePath": "Data/WM-Hair.Zl",
      "fileName": "WM-Hair.Zl"
    },
    {
      "libraryFile": "M_HumA",
      "sourcePath": "Data/M-HumA.Zl",
      "fileName": "M-HumA.Zl"
    },
    {
      "libraryFile": "M_HumAEx1",
      "sourcePath": "Data/M-HumAEx1.Zl",
      "fileName": "M-HumAEx1.Zl"
    },
    {
      "libraryFile": "M_HumAEx2",
      "sourcePath": "Data/M-HumAEx2.Zl",
      "fileName": "M-HumAEx2.Zl"
    },
    {
      "libraryFile": "M_HumAEx3",
      "sourcePath": "Data/M-HumAEx3.Zl",
      "fileName": "M-HumAEx3.Zl"
    },
    {
      "libraryFile": "WM_HumA",
      "sourcePath": "Data/WM-HumA.Zl",
      "fileName": "WM-HumA.Zl"
    },
    {
      "libraryFile": "WM_HumAEx1",
      "sourcePath": "Data/WM-HumAEx1.Zl",
      "fileName": "WM-HumAEx1.Zl"
    },
    {
      "libraryFile": "WM_HumAEx2",
      "sourcePath": "Data/WM-HumAEx2.Zl",
      "fileName": "WM-HumAEx2.Zl"
    },
    {
      "libraryFile": "WM_HumAEx3",
      "sourcePath": "Data/WM-HumAEx3.Zl",
      "fileName": "WM-HumAEx3.Zl"
    },
    {
      "libraryFile": "M_HumACx1",
      "sourcePath": "Data/M-HumACx1.Zl",
      "fileName": "M-HumACx1.Zl"
    },
    {
      "libraryFile": "WM_HumACx1",
      "sourcePath": "Data/WM-HumACx1.Zl",
      "fileName": "WM-HumACx1.Zl"
    },
    {
      "libraryFile": "M_HairA",
      "sourcePath": "Data/M-HairA.Zl",
      "fileName": "M-HairA.Zl"
    },
    {
      "libraryFile": "WM_HairA",
      "sourcePath": "Data/WM-HairA.Zl",
      "fileName": "WM-HairA.Zl"
    },
    {
      "libraryFile": "M_Costume",
      "sourcePath": "Data/M-Costume.Zl",
      "fileName": "M-Costume.Zl"
    },
    {
      "libraryFile": "M_CostumeA",
      "sourcePath": "Data/M-CostumeA.Zl",
      "fileName": "M-CostumeA.Zl"
    },
    {
      "libraryFile": "M_CostumeEx1",
      "sourcePath": "Data/M-CostumeEx1.Zl",
      "fileName": "M-CostumeEx1.Zl"
    },
    {
      "libraryFile": "WM_Costume",
      "sourcePath": "Data/WM-Costume.Zl",
      "fileName": "WM-Costume.Zl"
    },
    {
      "libraryFile": "WM_CostumeA",
      "sourcePath": "Data/WM-CostumeA.Zl",
      "fileName": "WM-CostumeA.Zl"
    },
    {
      "libraryFile": "WM_CostumeEx1",
      "sourcePath": "Data/WM-CostumeEx1.Zl",
      "fileName": "WM-CostumeEx1.Zl"
    },
    {
      "libraryFile": "Horse",
      "sourcePath": "Data/Horse.Zl",
      "fileName": "Horse.Zl"
    },
    {
      "libraryFile": "HorseIron",
      "sourcePath": "Data/Horse_Iron.Zl",
      "fileName": "Horse_Iron.Zl"
    },
    {
      "libraryFile": "HorseSilver",
      "sourcePath": "Data/Horse_Silver.Zl",
      "fileName": "Horse_Silver.Zl"
    },
    {
      "libraryFile": "HorseGold",
      "sourcePath": "Data/Horse_Golden.Zl",
      "fileName": "Horse_Golden.Zl"
    },
    {
      "libraryFile": "HorseBlue",
      "sourcePath": "Data/Horse_Blue.Zl",
      "fileName": "Horse_Blue.Zl"
    },
    {
      "libraryFile": "HorseDark",
      "sourcePath": "Data/Horse_Dark.Zl",
      "fileName": "Horse_Dark.Zl"
    },
    {
      "libraryFile": "HorseDarkEffect",
      "sourcePath": "Data/Horse_DarkEffect.Zl",
      "fileName": "Horse_DarkEffect.Zl"
    },
    {
      "libraryFile": "HorseRoyal",
      "sourcePath": "Data/Horse_Royal.Zl",
      "fileName": "Horse_Royal.Zl"
    },
    {
      "libraryFile": "HorseRoyalEffect",
      "sourcePath": "Data/Horse_RoyalEffect.Zl",
      "fileName": "Horse_RoyalEffect.Zl"
    },
    {
      "libraryFile": "HorseBlueDragon",
      "sourcePath": "Data/Horse_BlueDragon.Zl",
      "fileName": "Horse_BlueDragon.Zl"
    },
    {
      "libraryFile": "HorseBlueDragonEffect",
      "sourcePath": "Data/Horse_BlueDragonEffect.Zl",
      "fileName": "Horse_BlueDragonEffect.Zl"
    },
    {
      "libraryFile": "M_Shield1",
      "sourcePath": "Data/M-Shield1.Zl",
      "fileName": "M-Shield1.Zl"
    },
    {
      "libraryFile": "M_Shield2",
      "sourcePath": "Data/M-Shield2.Zl",
      "fileName": "M-Shield2.Zl"
    },
    {
      "libraryFile": "WM_Shield1",
      "sourcePath": "Data/WM-Shield1.Zl",
      "fileName": "WM-Shield1.Zl"
    },
    {
      "libraryFile": "WM_Shield2",
      "sourcePath": "Data/WM-Shield2.Zl",
      "fileName": "WM-Shield2.Zl"
    },
    {
      "libraryFile": "M_Weapon1",
      "sourcePath": "Data/M-Weapon1.Zl",
      "fileName": "M-Weapon1.Zl"
    },
    {
      "libraryFile": "M_Weapon2",
      "sourcePath": "Data/M-Weapon2.Zl",
      "fileName": "M-Weapon2.Zl"
    },
    {
      "libraryFile": "M_Weapon3",
      "sourcePath": "Data/M-Weapon3.Zl",
      "fileName": "M-Weapon3.Zl"
    },
    {
      "libraryFile": "M_Weapon4",
      "sourcePath": "Data/M-Weapon4.Zl",
      "fileName": "M-Weapon4.Zl"
    },
    {
      "libraryFile": "M_Weapon5",
      "sourcePath": "Data/M-Weapon5.Zl",
      "fileName": "M-Weapon5.Zl"
    },
    {
      "libraryFile": "M_Weapon6",
      "sourcePath": "Data/M-Weapon6.Zl",
      "fileName": "M-Weapon6.Zl"
    },
    {
      "libraryFile": "M_Weapon7",
      "sourcePath": "Data/M-Weapon7.Zl",
      "fileName": "M-Weapon7.Zl"
    },
    {
      "libraryFile": "M_Weapon10",
      "sourcePath": "Data/M-Weapon10.Zl",
      "fileName": "M-Weapon10.Zl"
    },
    {
      "libraryFile": "M_Weapon11",
      "sourcePath": "Data/M-Weapon11.Zl",
      "fileName": "M-Weapon11.Zl"
    },
    {
      "libraryFile": "M_Weapon12",
      "sourcePath": "Data/M-Weapon12.Zl",
      "fileName": "M-Weapon12.Zl"
    },
    {
      "libraryFile": "M_Weapon13",
      "sourcePath": "Data/M-Weapon13.Zl",
      "fileName": "M-Weapon13.Zl"
    },
    {
      "libraryFile": "M_Weapon14",
      "sourcePath": "Data/M-Weapon14.Zl",
      "fileName": "M-Weapon14.Zl"
    },
    {
      "libraryFile": "M_Weapon15",
      "sourcePath": "Data/M-Weapon15.Zl",
      "fileName": "M-Weapon15.Zl"
    },
    {
      "libraryFile": "M_Weapon16",
      "sourcePath": "Data/M-Weapon16.Zl",
      "fileName": "M-Weapon16.Zl"
    },
    {
      "libraryFile": "WM_Weapon1",
      "sourcePath": "Data/WM-Weapon1.Zl",
      "fileName": "WM-Weapon1.Zl"
    },
    {
      "libraryFile": "WM_Weapon2",
      "sourcePath": "Data/WM-Weapon2.Zl",
      "fileName": "WM-Weapon2.Zl"
    },
    {
      "libraryFile": "WM_Weapon3",
      "sourcePath": "Data/WM-Weapon3.Zl",
      "fileName": "WM-Weapon3.Zl"
    },
    {
      "libraryFile": "WM_Weapon4",
      "sourcePath": "Data/WM-Weapon4.Zl",
      "fileName": "WM-Weapon4.Zl"
    },
    {
      "libraryFile": "WM_Weapon5",
      "sourcePath": "Data/WM-Weapon5.Zl",
      "fileName": "WM-Weapon5.Zl"
    },
    {
      "libraryFile": "WM_Weapon6",
      "sourcePath": "Data/WM-Weapon6.Zl",
      "fileName": "WM-Weapon6.Zl"
    },
    {
      "libraryFile": "WM_Weapon7",
      "sourcePath": "Data/WM-Weapon7.Zl",
      "fileName": "WM-Weapon7.Zl"
    },
    {
      "libraryFile": "WM_Weapon10",
      "sourcePath": "Data/WM-Weapon10.Zl",
      "fileName": "WM-Weapon10.Zl"
    },
    {
      "libraryFile": "WM_Weapon11",
      "sourcePath": "Data/WM-Weapon11.Zl",
      "fileName": "WM-Weapon11.Zl"
    },
    {
      "libraryFile": "WM_Weapon12",
      "sourcePath": "Data/WM-Weapon12.Zl",
      "fileName": "WM-Weapon12.Zl"
    },
    {
      "libraryFile": "WM_Weapon13",
      "sourcePath": "Data/WM-Weapon13.Zl",
      "fileName": "WM-Weapon13.Zl"
    },
    {
      "libraryFile": "WM_Weapon14",
      "sourcePath": "Data/WM-Weapon14.Zl",
      "fileName": "WM-Weapon14.Zl"
    },
    {
      "libraryFile": "WM_Weapon15",
      "sourcePath": "Data/WM-Weapon15.Zl",
      "fileName": "WM-Weapon15.Zl"
    },
    {
      "libraryFile": "WM_Weapon16",
      "sourcePath": "Data/WM-Weapon16.Zl",
      "fileName": "WM-Weapon16.Zl"
    },
    {
      "libraryFile": "M_WeaponADL1",
      "sourcePath": "Data/M-WeaponADL1.Zl",
      "fileName": "M-WeaponADL1.Zl"
    },
    {
      "libraryFile": "M_WeaponADL2",
      "sourcePath": "Data/M-WeaponADL2.Zl",
      "fileName": "M-WeaponADL2.Zl"
    },
    {
      "libraryFile": "M_WeaponADL6",
      "sourcePath": "Data/M-WeaponADL6.Zl",
      "fileName": "M-WeaponADL6.Zl"
    },
    {
      "libraryFile": "M_WeaponADR1",
      "sourcePath": "Data/M-WeaponADR1.Zl",
      "fileName": "M-WeaponADR1.Zl"
    },
    {
      "libraryFile": "M_WeaponADR2",
      "sourcePath": "Data/M-WeaponADR2.Zl",
      "fileName": "M-WeaponADR2.Zl"
    },
    {
      "libraryFile": "M_WeaponADR6",
      "sourcePath": "Data/M-WeaponADR6.Zl",
      "fileName": "M-WeaponADR6.Zl"
    },
    {
      "libraryFile": "M_WeaponAOH1",
      "sourcePath": "Data/M-WeaponAOH1.Zl",
      "fileName": "M-WeaponAOH1.Zl"
    },
    {
      "libraryFile": "M_WeaponAOH2",
      "sourcePath": "Data/M-WeaponAOH2.Zl",
      "fileName": "M-WeaponAOH2.Zl"
    },
    {
      "libraryFile": "M_WeaponAOH3",
      "sourcePath": "Data/M-WeaponAOH3.Zl",
      "fileName": "M-WeaponAOH3.Zl"
    },
    {
      "libraryFile": "M_WeaponAOH4",
      "sourcePath": "Data/M-WeaponAOH4.Zl",
      "fileName": "M-WeaponAOH4.Zl"
    },
    {
      "libraryFile": "M_WeaponAOH5",
      "sourcePath": "Data/M-WeaponAOH5.Zl",
      "fileName": "M-WeaponAOH5.Zl"
    },
    {
      "libraryFile": "M_WeaponAOH6",
      "sourcePath": "Data/M-WeaponAOH6.Zl",
      "fileName": "M-WeaponAOH6.Zl"
    },
    {
      "libraryFile": "WM_WeaponADL1",
      "sourcePath": "Data/WM-WeaponADL1.Zl",
      "fileName": "WM-WeaponADL1.Zl"
    },
    {
      "libraryFile": "WM_WeaponADL2",
      "sourcePath": "Data/WM-WeaponADL2.Zl",
      "fileName": "WM-WeaponADL2.Zl"
    },
    {
      "libraryFile": "WM_WeaponADL6",
      "sourcePath": "Data/WM-WeaponADL6.Zl",
      "fileName": "WM-WeaponADL6.Zl"
    },
    {
      "libraryFile": "WM_WeaponADR1",
      "sourcePath": "Data/WM-WeaponADR1.Zl",
      "fileName": "WM-WeaponADR1.Zl"
    },
    {
      "libraryFile": "WM_WeaponADR2",
      "sourcePath": "Data/WM-WeaponADR2.Zl",
      "fileName": "WM-WeaponADR2.Zl"
    },
    {
      "libraryFile": "WM_WeaponADR6",
      "sourcePath": "Data/WM-WeaponADR6.Zl",
      "fileName": "WM-WeaponADR6.Zl"
    },
    {
      "libraryFile": "WM_WeaponAOH1",
      "sourcePath": "Data/WM-WeaponAOH1.Zl",
      "fileName": "WM-WeaponAOH1.Zl"
    },
    {
      "libraryFile": "WM_WeaponAOH2",
      "sourcePath": "Data/WM-WeaponAOH2.Zl",
      "fileName": "WM-WeaponAOH2.Zl"
    },
    {
      "libraryFile": "WM_WeaponAOH3",
      "sourcePath": "Data/WM-WeaponAOH3.Zl",
      "fileName": "WM-WeaponAOH3.Zl"
    },
    {
      "libraryFile": "WM_WeaponAOH4",
      "sourcePath": "Data/WM-WeaponAOH4.Zl",
      "fileName": "WM-WeaponAOH4.Zl"
    },
    {
      "libraryFile": "WM_WeaponAOH5",
      "sourcePath": "Data/WM-WeaponAOH5.Zl",
      "fileName": "WM-WeaponAOH5.Zl"
    },
    {
      "libraryFile": "WM_WeaponAOH6",
      "sourcePath": "Data/WM-WeaponAOH6.Zl",
      "fileName": "WM-WeaponAOH6.Zl"
    },
    {
      "libraryFile": "M_Helmet1",
      "sourcePath": "Data/M-Helmet1.Zl",
      "fileName": "M-Helmet1.Zl"
    },
    {
      "libraryFile": "M_Helmet2",
      "sourcePath": "Data/M-Helmet2.Zl",
      "fileName": "M-Helmet2.Zl"
    },
    {
      "libraryFile": "M_Helmet3",
      "sourcePath": "Data/M-Helmet3.Zl",
      "fileName": "M-Helmet3.Zl"
    },
    {
      "libraryFile": "M_Helmet4",
      "sourcePath": "Data/M-Helmet4.Zl",
      "fileName": "M-Helmet4.Zl"
    },
    {
      "libraryFile": "M_Helmet5",
      "sourcePath": "Data/M-Helmet5.Zl",
      "fileName": "M-Helmet5.Zl"
    },
    {
      "libraryFile": "M_Helmet11",
      "sourcePath": "Data/M-Helmet11.Zl",
      "fileName": "M-Helmet11.Zl"
    },
    {
      "libraryFile": "M_Helmet12",
      "sourcePath": "Data/M-Helmet12.Zl",
      "fileName": "M-Helmet12.Zl"
    },
    {
      "libraryFile": "M_Helmet13",
      "sourcePath": "Data/M-Helmet13.Zl",
      "fileName": "M-Helmet13.Zl"
    },
    {
      "libraryFile": "M_Helmet14",
      "sourcePath": "Data/M-Helmet14.Zl",
      "fileName": "M-Helmet14.Zl"
    },
    {
      "libraryFile": "WM_Helmet1",
      "sourcePath": "Data/WM-Helmet1.Zl",
      "fileName": "WM-Helmet1.Zl"
    },
    {
      "libraryFile": "WM_Helmet2",
      "sourcePath": "Data/WM-Helmet2.Zl",
      "fileName": "WM-Helmet2.Zl"
    },
    {
      "libraryFile": "WM_Helmet3",
      "sourcePath": "Data/WM-Helmet3.Zl",
      "fileName": "WM-Helmet3.Zl"
    },
    {
      "libraryFile": "WM_Helmet4",
      "sourcePath": "Data/WM-Helmet4.Zl",
      "fileName": "WM-Helmet4.Zl"
    },
    {
      "libraryFile": "WM_Helmet5",
      "sourcePath": "Data/WM-Helmet5.Zl",
      "fileName": "WM-Helmet5.Zl"
    },
    {
      "libraryFile": "WM_Helmet11",
      "sourcePath": "Data/WM-Helmet11.Zl",
      "fileName": "WM-Helmet11.Zl"
    },
    {
      "libraryFile": "WM_Helmet12",
      "sourcePath": "Data/WM-Helmet12.Zl",
      "fileName": "WM-Helmet12.Zl"
    },
    {
      "libraryFile": "WM_Helmet13",
      "sourcePath": "Data/WM-Helmet13.Zl",
      "fileName": "WM-Helmet13.Zl"
    },
    {
      "libraryFile": "WM_Helmet14",
      "sourcePath": "Data/WM-Helmet14.Zl",
      "fileName": "WM-Helmet14.Zl"
    },
    {
      "libraryFile": "M_HelmetCx1",
      "sourcePath": "Data/M-HelmetCx1.Zl",
      "fileName": "M-HelmetCx1.Zl"
    },
    {
      "libraryFile": "WM_HelmetCx1",
      "sourcePath": "Data/WM-HelmetCx1.Zl",
      "fileName": "WM-HelmetCx1.Zl"
    },
    {
      "libraryFile": "M_HelmetA1",
      "sourcePath": "Data/M-HelmetA1.Zl",
      "fileName": "M-HelmetA1.Zl"
    },
    {
      "libraryFile": "M_HelmetA2",
      "sourcePath": "Data/M-HelmetA2.Zl",
      "fileName": "M-HelmetA2.Zl"
    },
    {
      "libraryFile": "M_HelmetA3",
      "sourcePath": "Data/M-HelmetA3.Zl",
      "fileName": "M-HelmetA3.Zl"
    },
    {
      "libraryFile": "M_HelmetA4",
      "sourcePath": "Data/M-HelmetA4.Zl",
      "fileName": "M-HelmetA4.Zl"
    },
    {
      "libraryFile": "WM_HelmetA1",
      "sourcePath": "Data/WM-HelmetA1.Zl",
      "fileName": "WM-HelmetA1.Zl"
    },
    {
      "libraryFile": "WM_HelmetA2",
      "sourcePath": "Data/WM-HelmetA2.Zl",
      "fileName": "WM-HelmetA2.Zl"
    },
    {
      "libraryFile": "WM_HelmetA3",
      "sourcePath": "Data/WM-HelmetA3.Zl",
      "fileName": "WM-HelmetA3.Zl"
    },
    {
      "libraryFile": "WM_HelmetA4",
      "sourcePath": "Data/WM-HelmetA4.Zl",
      "fileName": "WM-HelmetA4.Zl"
    },
    {
      "libraryFile": "M_HelmetACx1",
      "sourcePath": "Data/M-HelmetACx1.Zl",
      "fileName": "M-HelmetACx1.Zl"
    },
    {
      "libraryFile": "WM_HelmetACx1",
      "sourcePath": "Data/WM-HelmetACx1.Zl",
      "fileName": "WM-HelmetACx1.Zl"
    }
  ],
  "playerConstants": {
    "FemaleOffSet": 5000,
    "AssassinOffSet": 50000,
    "RightHandOffSet": 50
  },
  "playerLibrarySelectors": {
    "ArmourList": {
      "0": "M_Hum",
      "1": "M_HumEx1",
      "2": "M_HumEx2",
      "3": "M_HumEx3",
      "4": "M_HumEx4",
      "10": "M_HumEx10",
      "11": "M_HumEx11",
      "12": "M_HumEx12",
      "13": "M_HumEx13",
      "20": "M_HumCx1",
      "5000": "WM_Hum",
      "5001": "WM_HumEx1",
      "5002": "WM_HumEx2",
      "5003": "WM_HumEx3",
      "5004": "WM_HumEx4",
      "5010": "WM_HumEx10",
      "5011": "WM_HumEx11",
      "5012": "WM_HumEx12",
      "5013": "WM_HumEx13",
      "5020": "WM_HumCx1",
      "50000": "M_HumA",
      "50001": "M_HumAEx1",
      "50002": "M_HumAEx2",
      "50003": "M_HumAEx3",
      "50020": "M_HumACx1",
      "55000": "WM_HumA",
      "55001": "WM_HumAEx1",
      "55002": "WM_HumAEx2",
      "55003": "WM_HumAEx3",
      "55020": "WM_HumACx1"
    },
    "CostumeList": {
      "0": "M_Costume",
      "1": "M_CostumeEx1",
      "5000": "WM_Costume",
      "5001": "WM_CostumeEx1",
      "50000": "M_CostumeA",
      "55000": "WM_CostumeA"
    },
    "WeaponList": {
      "0": "M_Weapon1",
      "1": "M_Weapon2",
      "2": "M_Weapon3",
      "3": "M_Weapon4",
      "4": "M_Weapon5",
      "5": "M_Weapon6",
      "6": "M_Weapon7",
      "9": "M_Weapon10",
      "10": "M_Weapon11",
      "11": "M_Weapon12",
      "12": "M_Weapon13",
      "13": "M_Weapon14",
      "14": "M_Weapon15",
      "15": "M_Weapon16",
      "5000": "WM_Weapon1",
      "5001": "WM_Weapon2",
      "5002": "WM_Weapon3",
      "5003": "WM_Weapon4",
      "5004": "WM_Weapon5",
      "5005": "WM_Weapon6",
      "5006": "WM_Weapon7",
      "5009": "WM_Weapon10",
      "5010": "WM_Weapon11",
      "5011": "WM_Weapon12",
      "5012": "WM_Weapon13",
      "5013": "WM_Weapon14",
      "5014": "WM_Weapon15",
      "5015": "WM_Weapon16",
      "110": "M_WeaponAOH1",
      "111": "M_WeaponAOH2",
      "112": "M_WeaponAOH3",
      "113": "M_WeaponAOH4",
      "114": "M_WeaponAOH5",
      "115": "M_WeaponAOH6",
      "5110": "WM_WeaponAOH1",
      "5111": "WM_WeaponAOH2",
      "5112": "WM_WeaponAOH3",
      "5113": "WM_WeaponAOH4",
      "5114": "WM_WeaponAOH5",
      "5115": "WM_WeaponAOH6",
      "120": "M_WeaponADL1",
      "121": "M_WeaponADL2",
      "125": "M_WeaponADL6",
      "170": "M_WeaponADR1",
      "171": "M_WeaponADR2",
      "175": "M_WeaponADR6",
      "5120": "WM_WeaponADL1",
      "5121": "WM_WeaponADL2",
      "5125": "WM_WeaponADL6",
      "5170": "WM_WeaponADR1",
      "5171": "WM_WeaponADR2",
      "5175": "WM_WeaponADR6"
    },
    "ShieldList": {
      "0": "M_Shield1",
      "1": "M_Shield2",
      "5000": "WM_Shield1",
      "5001": "WM_Shield2"
    },
    "HelmetList": {
      "0": "M_Helmet1",
      "1": "M_Helmet2",
      "2": "M_Helmet3",
      "3": "M_Helmet4",
      "4": "M_Helmet5",
      "10": "M_Helmet11",
      "11": "M_Helmet12",
      "12": "M_Helmet13",
      "13": "M_Helmet14",
      "20": "M_HelmetCx1",
      "5000": "WM_Helmet1",
      "5001": "WM_Helmet2",
      "5002": "WM_Helmet3",
      "5003": "WM_Helmet4",
      "5004": "WM_Helmet5",
      "5010": "WM_Helmet11",
      "5011": "WM_Helmet12",
      "5012": "WM_Helmet13",
      "5013": "WM_Helmet14",
      "5020": "WM_HelmetCx1",
      "50000": "M_HelmetA1",
      "50001": "M_HelmetA2",
      "50002": "M_HelmetA3",
      "50003": "M_HelmetA4",
      "50020": "M_HelmetACx1",
      "55000": "WM_HelmetA1",
      "55001": "WM_HelmetA2",
      "55002": "WM_HelmetA3",
      "55003": "WM_HelmetA4",
      "55020": "WM_HelmetACx1"
    }
  },
  "drawFrameFormula": "frameIndex + startIndex + offset * direction",
  "pushedPlayerFrameOverride": 0,
  "notes": [
    "All player frame definitions are extracted from FrameSet.Players.",
    "Magic-to-body-animation cases are extracted from Functions.GetMagicAnimation.",
    "Armour/Costume/Weapon/Shield/Helmet selectors are extracted from PlayerObject dictionaries.",
    "Real PNG/atlas payload is generated only when the corresponding Zircon .Zl files are supplied.",
    "No Crystal fallback is permitted."
  ]
});
export const ZIRCON_PLAYER_FRAMESET = ZIRCON_PLAYER_ASSET_CONTRACT.playerFrames;
export const ZIRCON_MIR_ANIMATION = ZIRCON_PLAYER_ASSET_CONTRACT.mirAnimation;
export const ZIRCON_MAGIC_ANIMATION_MAP = ZIRCON_PLAYER_ASSET_CONTRACT.magicAnimationMap;
export const ZIRCON_PLAYER_LIBRARY_SELECTORS = ZIRCON_PLAYER_ASSET_CONTRACT.playerLibrarySelectors;
