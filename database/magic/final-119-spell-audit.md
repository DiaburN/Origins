# ORIGINS — final 119-spell audit

Branch: `work/spells-final-audit`

Pinned sources:

- Zircon runtime/database: `Suprcode/Zircon@cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Crystal base spell source: `Suprcode/Crystal@0e315fe327192afe52c3d7357ddd1f5b7e26c5b8`
- Crystal-Monk extension source: `JevLOMCN/Crystal-Monk@381e589e3d7ee736cdf0583c8315c0d144ab058f`
- Crystal.Database/Jev values: `a19f6dca8f5e238d4ed79801820777abbf0a9ca4`

## Final playable scope

ORIGINS activates five playable classes and 119 catalogue spells:

| Class | Spell count | Compiled runtime routes | Source stubs |
|---|---:|---:|---:|
| Warrior | 21 | 21 | 0 |
| Wizard | 28 | 27 | 1 |
| Taoist | 27 | 27 | 0 |
| Assassin | 19 | 19 | 0 |
| Archer | 24 | 24 | 0 |
| **Total** | **119** | **118** | **1** |

The nine Monk spells from Crystal-Monk are retained under `deferredClasses.Monk` in `crystal-playable-spells.json` but are not part of the active runtime. `includeMonk=false`. The source Monk kit remains deferred because nine skills is materially incomplete compared with the five active classes.

`FastMove` is the single intentional source stub. The pinned Crystal source contains only an unfinished/commented placeholder and does not expose usable `MagicInfo` plus server execution behavior. ORIGINS preserves the identity and does not fabricate numerics or runtime behavior.

## Runtime and handler validation — CLOSED

The complete five-class runtime patch set now applies cleanly to the pinned Zircon revision using exact-context patch application.

Validated result:

- active catalogue entries: **119**;
- routed runtime behaviors: **118**;
- registered `MagicObject` handlers: **118/118**;
- source stubs: **1** (`FastMove`);
- source-ported but uncompiled routes: **0**;
- `LibraryCore` compile: **PASS**;
- `ServerLibrary` compile: **PASS**;
- Monk runtime routes: **0**.

The handler verifier requires exactly one compatible `MagicObject` registration for every routed active `MagicType`; renamed native mappings such as `Fencing -> Swordsmanship`, `Healing -> Heal`, `Teleport -> Teleportation` and other intentional mappings are therefore checked rather than inferred from spell names alone.

Compilation proves integration/type correctness and registration coverage. It does not replace full in-game behavioral smoke testing of every spell family.

## MagicType and custom-stat audit

The ORIGINS custom MagicType ranges are separated by class and do not overlap:

- Warrior: `1100–1114`
- Wizard: `1200–1217`
- Taoist: `1300–1313`
- Assassin: `1400–1418`
- Archer: `1500–1523`

Existing Zircon identities are reused when the source behavior genuinely maps to them; Crystal-specific/incompatible abilities use the reserved ORIGINS blocks.

The server-only custom Stat IDs used by the magic port are also separated after the final compile audit:

- `11000–11004`: Wizard/Warrior runtime additions;
- `11005–11007`: Taoist runtime additions;
- `11008–11011`: Archer runtime additions.

## Patch hygiene — CLOSED

Historical malformed/stale pseudo-diffs are applied through `scripts/apply-origins-patches.py`, which ignores stale hunk line-number metadata but requires every old-context block to match exactly once. Missing or ambiguous context is fatal; no fuzzy application is allowed.

The obsolete patch that introduced Monk as an active class was removed. Superseded Archer delayed-explosion/pet-expiry patches were also removed after their behavior was consolidated into the active Archer runtime patch. Monk remains absent from the active patch chain.

## Crystal/Jev numeric-source hygiene — CLOSED

The numeric pipeline now distinguishes current source identity from historical database labels:

- Crystal source comments are masked before `MagicInfo` extraction, so the commented `FastMove` placeholder cannot become invented data;
- Crystal-Monk spell IDs are parsed only from `Common.cs::Spell`, preventing collisions with identically named members in enums such as `PoisonType`;
- Jev projection uses current Crystal spell identity and keeps legacy/unknown rows as audit evidence;
- custom/map-event rows do not enter the 119-spell player runtime merge;
- ambiguous playable duplicates cannot be selected by input order.

## Final System.db projection — CLOSED

GitHub Actions run `32308650321` (`ORIGINS System DB`) completed successfully on validated head `a4e599c3b925c833ffdcd25f68988d23f6dfa6f9`.

The generated active magic overlay contains exactly:

- **119** `MagicInfo` operations;
- **118** compiled runtime routes bound to real patched-Zircon `MagicType` values;
- **1** disabled source-stub row (`FastMove`);
- **0** pending runtime placeholders;
- **27** routed spells reusing native Zircon `MagicInfo` identities;
- **91** routed spells using ORIGINS runtime mappings.

Applying the overlay to the pinned Zircon snapshot completed with:

- **90 created** rows;
- **29 updated** rows;
- **0 deleted** rows;
- **119 total operations**.

The rebuilt database passed import, verification and audit preflight. Final generated database metadata:

- System version: `2026.08.19.1`
- System.db SHA-256: `7df0446b804b6d95b1b192ae3d32570bb9f9ecbb3d5cb3827ca288cbee11cdbb`
- artifact: `origins-system-db`

The existing Users.db smoke also passed against this final System.db: account, character and learned-magic persistence round-tripped successfully with Wizard `FireBall`.

## CI result for the final validated magic state

On head `a4e599c3b925c833ffdcd25f68988d23f6dfa6f9`, all six relevant gates completed successfully:

1. `Crystal Magic Catalogue` — PASS
2. `Spell Patch Apply` — PASS
3. `Spell Runtime Compile` — PASS
4. `Magic Candidate Validation` — PASS
5. `Database Foundation` — PASS
6. `ORIGINS System DB` — PASS

## Remaining work after database activation

The source migration, compile gate and full numeric System.db projection are closed. Remaining work is runtime/content/client validation rather than additional spell discovery:

1. Run representative in-game smoke tests for attack skills, persistent fields, buffs, summons, poison/control states and movement skills across all five classes.
2. Expand learned-magic Users.db round-trip coverage beyond the existing Wizard/FireBall smoke to include at least one spell from every active class.
3. Bind the Reincarnation request/accept/cancel protocol to the client/mobile confirmation UI.
4. Decide and persist Archer `MentalState` and elemental-orb progress if persistence is required; the current port intentionally keeps them as runtime state.
5. During the monster/content database phase, ensure the Archer summon dependencies exist for VampireSpider, SpittingToad, SnakeTotem and StoneTrap, plus any other spell-required pet definitions.
6. Bind Crystal client icons, casting choreography, projectile/impact effects and mobile UI separately. Visual readiness is not inferred from server/runtime readiness.

## Audit conclusion

The magic migration is now closed at the **server source + compilation + System.db integration** level:

- **5 active classes**;
- **119 catalogue spells**;
- **118 compiled and DB-activated runtime routes**;
- **1 intentional source stub (`FastMove`)**;
- **9 Monk spells deferred and inactive**;
- **0 pending runtime placeholders**;
- final System.db build/verify/audit: **PASS**.

The next magic milestone is no longer migration or database construction. It is **in-game behavioral smoke testing and client visual/UI binding**.
