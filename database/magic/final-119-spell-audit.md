# ORIGINS — final 119-spell audit

Branch: `work/spells-final-audit`

Pinned sources:

- Zircon runtime/database: `Suprcode/Zircon@cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Crystal base spell source: `Suprcode/Crystal@0e315fe327192afe52c3d7357ddd1f5b7e26c5b8`
- Crystal-Monk extension source: `JevLOMCN/Crystal-Monk@381e589e3d7ee736cdf0583c8315c0d144ab058f`

## Final playable scope

ORIGINS currently activates five playable classes and 119 catalogue spells:

| Class | Spell count |
|---|---:|
| Warrior | 21 |
| Wizard | 28 |
| Taoist | 27 |
| Assassin | 19 |
| Archer | 24 |
| **Total** | **119** |

The nine Monk spells from Crystal-Monk are retained under `deferredClasses.Monk` in `crystal-playable-spells.json` but are not part of the active runtime. The source Monk kit is intentionally deferred because nine spells is materially incomplete compared with the other classes.

## Coverage result

- Active catalogue entries: **119**
- Entries with an identified/ported runtime behavior route: **118**
- Source stubs deliberately left without invented behavior: **1** (`FastMove`)
- Missing active-catalogue behavior decisions: **0**
- Monk runtime patches in this branch: **0**

`FastMove` is not treated as a defect in the port. The pinned Crystal source does not expose usable `MagicInfo` plus server execution behavior for it, so ORIGINS records the source stub instead of fabricating a spell.

## Runtime readiness

Current readiness must not be confused with source-port coverage:

| State | Count |
|---|---:|
| Previously compile/runtime validated Wizard routes | 15 |
| Source-ported but not yet compile-validated | 103 |
| Source stub | 1 |
| **Total** | **119** |

Warrior, Taoist, Assassin and Archer remain `runtimeReady=false` until their accumulated patch series is applied to a clean copy of the pinned Zircon source and compiled. The newer Wizard batches also remain false for the same reason.

This audit therefore closes **source/runtime design coverage**, not the final compile gate.

## MagicType range audit

The ORIGINS custom ranges are separated by class and do not overlap:

- Warrior: `1100–1114`
- Wizard: `1200–1217`
- Taoist: `1300–1313`
- Assassin: `1400–1418`
- Archer: `1500–1523`

Existing Zircon identities continue to be reused when source behavior genuinely maps to them; the custom blocks are for Crystal-specific or incompatible behavior.

## Patch hygiene corrections made during this audit

The obsolete `patches/zircon/007-crystal-playable-classes.patch` was removed. It duplicated the Archer class extension later owned by patch 022 and still introduced `Monk = 5` / `RequiredClass.Monk`, which conflicted with the final five-class scope.

After removal:

- patch 022 is the single active Archer class/identity patch;
- no active patch adds the Monk class;
- no `027-crystal-monk-*` runtime patch exists on the final audit branch;
- numbering gaps in the patch directory are intentional and harmless.

## Database projection status

The authoring overlay `database/overlays/70-magics-crystal.json` remains empty by design. A complete 119-spell System.db projection must not be written until the pending runtime patches compile against the pinned Zircon source.

There is an earlier proof branch, `generated/origins-system-db`, which contains a real generated `System.db` and proves the database pipeline works. That proof must be treated separately from the current 119-spell scope:

- generated System.db exists and passed database preflight;
- its generated magic overlay updated **5 existing MagicInfo rows**: FireBall, ThunderBolt, FireWall, MagicShield and IceStorm;
- the generated overlay preserved Zircon indices and joined Crystal/Jev data by normalized spell name rather than numeric spell ID;
- the old activation-status on that branch explicitly recorded System.db round-trip for **3 spells**: FireBall, ThunderBolt and IceStorm;
- the Users.db smoke test explicitly round-tripped one learned magic: Fire Ball;
- that branch contains stale catalogue IDs/status metadata and is **not** authoritative for the final 119-spell catalogue.

The final branch records this distinction in `activation-status.json`.

## Known remaining gates before full magic DB activation

1. Apply patches 001–026, excluding removed/absent gaps, against a clean copy of pinned Zircon in order and resolve any context conflicts.
2. Compile LibraryCore + ServerLibrary with all five-class changes together.
3. Run runtime smoke tests for attack skills, persistent fields, buffs, summons, poison/control states and movement skills.
4. Bind the Reincarnation request/accept/cancel packets to the client/mobile confirmation UI; the server protocol is already represented in patch 017.
5. Decide/persist Archer `MentalState` and elemental-orb progress after compile validation; the current port deliberately keeps them as runtime fields.
6. During the monster/database phase, ensure Crystal Archer summon records exist for VampireSpider, SpittingToad, SnakeTotem and StoneTrap, plus other spell-required pet definitions.
7. Generate the complete 119-spell numeric `MagicInfo` overlay from Crystal/Jev values by normalized spell name and build a fresh System.db.
8. Run System.db + Users.db round-trip tests across every class, not just the early Wizard proof.
9. Bind client icons/visual choreography separately; visual readiness must not be inferred from server runtime readiness.

## Audit conclusion

The magic migration is now structurally closed at **five active classes / 119 catalogue spells**. All active spells have a behavior decision; 118 have runtime routes and FastMove is the single intentional source stub. Monk is fully excluded from the active class/runtime patch chain while its source material remains retained for a possible future redesign.

The next technical magic milestone is **compile + full numeric System.db projection**, not more spell discovery.
