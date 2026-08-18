# ORIGINS — Crystal spells on Zircon runtime

## Decision

Do not copy Crystal's database engine and do not create a generic parallel spell engine.

The current official Zircon runtime already provides one class per spell under `ServerLibrary/Models/Magics/<Class>/`, based on `MagicObject` and registered with `[MagicType(...)]`.

Example flow from Zircon FireBall:

1. `MagicCast(...)` validates the target.
2. It records the target/location returned to the client.
3. It schedules `ActionType.DelayMagic` using distance-based timing.
4. `MagicComplete(...)` calls Zircon `Player.MagicAttack(...)`.
5. Power, element, augments, cooldown and leveling remain inside Zircon primitives.

This is already the compatibility layer we need.

## Crystal integration workflow

For every Crystal spell we record:

- Crystal spell name/id/class.
- Crystal call site and execution path.
- closest Zircon `MagicType` / `MagicObject`.
- cast target semantics.
- delay/projectile/impact timing.
- damage/buff/debuff/summon behavior.
- whether the mapping is native, Zircon-adapted or Crystal-adapted.

Only after that comparison is `Verified=true` written to `database/magic/execution-profiles.json`.

## Animation separation

Server combat timing and client visual choreography stay separate. ORIGINS can keep its validated cast/projectile/impact animation timing without moving damage calculation out of Zircon.
