# Crystal Archer static audit

Branch: `work/archer-crystal-batch1`

- Catalogue coverage: 24/24 identities have Zircon runtime routes.
- Runtime/client flags remain false until real compilation and client binding.
- `MirClass.Archer` and `MagicType` 1500-1523 are introduced as Zircon extensions.
- Normal ranged attack is adapted to Crystal distance DC, MentalState and Focus pre-hit probability.
- `Stat.PoisonAttack` is added at 11009 because the prior Taoist port already required the Crystal stat and pinned Zircon did not define it.
- DelayedExplosion uses a timed state and a 3x3 detonation route rather than an immediate second target hit.
- OneWithNature is the source offensive 5x5 behavior, not a healing skill.
- ORIGINS no-player-push policy is retained for ElementalShot; monster knockback remains.
- Archer summoned monster names are matched by Crystal source names (`VampireSpider`, `SpittingToad`, `SnakeTotem`, `StoneTrap`) and depend on the later monster/database projection providing those records.
- MentalState and elemental-orb state are currently runtime fields on `PlayerObject`; persistence is intentionally deferred to the database integration/compile pass.
