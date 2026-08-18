# ORIGINS database source policy

## Authoritative schema/runtime

ORIGINS follows the pinned official `Suprcode/Zircon` source. The MirDB engine, SystemModels, DBModels and server-side execution rules come from that source revision.

## Published content database

The public Zircon file index currently exposes `Database.7z` as the content database download. Its listed modification date is older than the pinned source runtime, so ORIGINS treats it as an **input dataset**, not as an already-current schema.

The build pipeline therefore never copies that `System.db` straight into ORIGINS production. It must pass this chain:

```text
Database.7z
 -> source preflight
 -> current Zircon mapping upgrade (staged copy)
 -> upgraded preflight
 -> complete index-preserving JSON snapshot
 -> ORIGINS overlays
 -> rebuild through current Zircon MirDB
 -> reopen + preflight + index validation
```

If any gate fails, the candidate is rejected.

## Crystal

Crystal is not a database source for ORIGINS. Crystal is consulted only for the spell catalogue and, where necessary, spell behavior. Crystal spell data is mapped into Zircon `MagicInfo`; execution remains Zircon `MagicObject`-based.

Monk content is intentionally deferred until the later item/set/stat phase.
