# ORIGINS MOBILE — Crystal Magic Source Policy

## Authoritative rule

This ORIGINS MOBILE project does **not** reuse the old Holley/Mir3 magic assets or the previous Holley magic-animation analysis.

For the new project:

- **Runtime/database architecture:** pinned official Zircon.
- **Player spell catalogue, numeric values and behavior source:** pinned Crystal + Crystal.Database/Jev.
- **Visual spell assets:** Crystal client/data assets only when the visual/client phase starts.
- **Character sprites, movement and casting animation:** handled later from the Crystal client assets; they are not taken from the previous Holley project.

## Current first Wizard package

The first complete runtime package is intentionally limited to the 15 Crystal Wizard spells already selected for implementation:

1. FireBall
2. ThunderBolt
3. FireWall
4. MagicShield
5. IceStorm
6. Repulsion
7. ElectricShock
8. GreatFireBall
9. HellFire
10. FireBang
11. Teleport
12. Lightning
13. FrostCrunch
14. ThunderStorm
15. TurnUndead

Existing Zircon handlers are reused only when they represent the same ability. Missing/different Crystal behaviors are implemented through Zircon `MagicObject` overrides or Crystal-only `MagicType` values in the reserved ORIGINS Wizard range 1200–1299.

No Holley visual assumptions are allowed to influence these spell implementations.
